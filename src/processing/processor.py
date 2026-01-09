"""Video generation processor with matrix handling."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from loguru import logger
from rich.progress import Progress

from ..api.client import ReplicateClient
from .input_discovery import discover_markdown_jobs, parse_markdown_job
from .profile_loader import load_active_profiles
from .cost_calculator import calculate_cost_from_params
from .output_generator import save_generation_files
from ..utils.filename_utils import generate_video_filename
from .duration_handler import (
    process_duration,
    get_duration_parameter_name,
    should_include_fps,
)
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MarkdownJob
from ..models.video_processing import VideoGenerationRequest
from .generation_logger import log_generation_start, log_generation_complete


def _create_run_directory(
    output_dir: Path, active_profiles: List[Dict[str, Any]]
) -> Path:
    """Create timestamped output directory for this run.
    If exactly one profile is active, use its name as the suffix.
    """
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    if len(active_profiles) == 1:
        # Sanitize profile name for filesystem
        profile_suffix = (
            str(active_profiles[0]["name"]).strip().replace("/", "-").replace(" ", "_")
        )
        dir_name = f"{timestamp}_{profile_suffix}"
    else:
        dir_name = f"{timestamp}_VIDEO"
    run_dir = output_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {run_dir}")
    return run_dir


def _process_all_videos(
    client: ReplicateClient,
    jobs: List[MarkdownJob],
    active_profiles: List[Dict[str, Any]],
    run_dir: Path,
    progress: Optional[Progress] = None,
) -> Tuple[int, float, List[Dict[str, Any]]]:
    """Process all video generations in the matrix."""
    total = len(jobs) * len(active_profiles)
    success_count = 0
    total_cost = 0.0
    all_adjustments = []

    task_id = None
    if progress:
        task_id = progress.add_task("Generating videos", total=total)

    for job in jobs:
        for profile in active_profiles:
            # Process single video
            video_cost, adjustment_info = _process_single_video(
                client, job, profile, run_dir
            )

            # Track adjustment if any
            if adjustment_info and adjustment_info.get("reason"):
                adjustment_record = {
                    "markdown_file": job.markdown_file.name,
                    "profile": profile["name"],
                    **adjustment_info,
                }
                all_adjustments.append(adjustment_record)

            success_count += 1
            total_cost += video_cost

            if progress and task_id is not None:
                progress.advance(task_id)

    return success_count, total_cost, all_adjustments


def process_matrix(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process markdown job files with profile matrix for video generation.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results

    Raises:
        Exception: On any processing failure (fail-fast)
    """
    # 1. Discover markdown job files
    markdown_files = discover_markdown_jobs(context.input_dir)
    logger.info(f"Found {len(markdown_files)} markdown job files")

    # 2. Parse markdown jobs
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]

    # 3. Load video profiles
    active_profiles = load_active_profiles(context.profiles_dir)
    logger.info(f"Loaded {len(active_profiles)} video profiles")

    # 4. Create timestamped output directory
    run_dir = _create_run_directory(context.output_dir, active_profiles)

    # 5. Process matrix sequentially
    total = len(jobs) * len(active_profiles)
    success_count, total_cost, all_adjustments = _process_all_videos(
        context.client, jobs, active_profiles, run_dir, context.progress
    )

    return {
        "total": total,
        "success": success_count,
        "failed": total - success_count,
        "cost": total_cost,
        "output_dir": run_dir,
        "adjustments": all_adjustments,
    }


def _apply_prompt_modifications(prompt: str, profile: Dict[str, Any]) -> str:
    """
    Apply prefix and suffix modifications to prompt based on profile configuration.

    Args:
        prompt: Original prompt text
        profile: Profile configuration dictionary

    Returns:
        Modified prompt with prefix/suffix applied

    Raises:
        ValueError: If final prompt is empty after modifications
    """
    # Strip whitespace from original prompt
    prompt = prompt.strip()

    # Apply prefix if configured
    prefix = profile.get("prompt_prefix")
    if prefix and prefix.strip():
        prompt = f"{prefix.strip()} {prompt}" if prompt else prefix.strip()

    # Apply suffix if configured
    suffix = profile.get("prompt_suffix")
    if suffix and suffix.strip():
        prompt = f"{prompt} {suffix.strip()}" if prompt else suffix.strip()

    # Final validation and normalize whitespace
    prompt = " ".join(prompt.split())
    if not prompt:
        raise ValueError("Final prompt is empty after applying modifications")

    return prompt


def _process_single_video(
    client: ReplicateClient, job: MarkdownJob, profile: Dict[str, Any], run_dir: Path
) -> Tuple[float, Dict[str, Any]]:
    """
    Process a single video generation from markdown job.

    Args:
        client: Replicate API client
        job: MarkdownJob with parsed data
        profile: Profile configuration
        run_dir: Output directory

    Returns:
        Tuple of (cost, adjustment_info)

    Raises:
        Exception: On generation failure
    """
    # Extract data from job
    prompt = job.prompt
    image_url = job.image_url
    num_frames = job.num_frames

    # Apply prompt modifications (prefix/suffix) if configured in profile
    original_prompt = prompt
    prompt = _apply_prompt_modifications(prompt, profile)

    # Create output directory
    video_dir = _create_video_directory(run_dir, job.markdown_file, profile)
    subfolder_name = video_dir.name

    logger.info(f"Processing: {subfolder_name}")

    try:
        # Prepare parameters with duration handling
        params, adjustment_info = _prepare_generation_params(profile, num_frames)

        # Log generation start
        log_generation_start(
            subfolder_name, profile, prompt, image_url, num_frames, params
        )

        # Generate and download video
        gen_request = VideoGenerationRequest(
            client=client,
            profile=profile,
            image_url=image_url,
            prompt=prompt,
            params=params,
            output_dir=video_dir,
            markdown_file=job.markdown_file,
        )
        video_url, video_path = _generate_and_download_video(gen_request)

        # Calculate cost based on actual video duration
        video_cost = calculate_cost_from_params(profile, params, num_frames)

        # Create generation context with all data
        # Note: We save the original prompt (without suffix) in context for documentation
        # The suffix was already applied and used in the API call above
        context = GenerationContext(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,  # Same file contains all data
            num_frames_file=job.markdown_file,  # Same file contains all data
            output_dir=video_dir,
            prompt=original_prompt,
            image_url=image_url,
            num_frames=num_frames,
            profile=profile,
            params=params,
            video_url=video_url,
            video_path=video_path,
            cost=video_cost,
            adjustment_info=adjustment_info,
        )

        # Save all documentation
        save_generation_files(context)

        # Log completion
        log_generation_complete(video_path, video_cost)

        return video_cost, adjustment_info

    except Exception as e:
        logger.error(f"Failed: {job.markdown_file.name} + {profile['name']}: {e}")
        raise  # Fail-fast philosophy


def _prepare_generation_params(
    profile: Dict[str, Any], num_frames: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Prepare API parameters with duration handling.

    Returns:
        Tuple of (params, adjustment_info)
    """
    params = profile["parameters"].copy()

    # Process duration based on profile configuration
    adjusted_duration, was_adjusted, adjustment_info = process_duration(
        num_frames, profile
    )

    # Get the correct parameter name from profile
    param_name = get_duration_parameter_name(profile)
    params[param_name] = adjusted_duration

    # Include fps if needed by the model
    if should_include_fps(profile):
        params["fps"] = profile["duration_config"]["fps"]

    return params, adjustment_info


def _create_video_directory(
    run_dir: Path, markdown_file: Path, profile: Dict[str, Any]
) -> Path:
    """Create output directory for video generation."""
    subfolder_name = f"{markdown_file.stem}_X_{profile['name']}"
    video_dir = run_dir / subfolder_name
    video_dir.mkdir(exist_ok=True)
    return video_dir


def _generate_and_download_video(request: VideoGenerationRequest) -> Tuple[str, Path]:
    """
    Generate video and download it.

    Args:
        request: VideoGenerationRequest with all required parameters

    Returns:
        Tuple of (video_url, video_path)
    """
    from .video_downloader import download_video

    # Generate video using Replicate API
    video_url = request.client.generate_video(
        model_name=request.profile["model_id"],
        image_url=request.image_url,
        prompt=request.prompt,
        params=request.params,
        image_url_param=request.profile.get("image_url_param", "image"),
    )

    if not video_url:
        raise Exception(f"Failed to generate video for {request.markdown_file.name}")

    # Download video to output directory
    video_filename = generate_video_filename(request.markdown_file.name)
    video_path = request.output_dir / video_filename
    download_video(video_url, video_path)

    return video_url, video_path
