"""Hybrid video processor using BOTH alive-progress AND Rich for maximum impact."""

# Standard library imports
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Third-party imports
from loguru import logger

# Local imports - API
from ..api.async_client_enhanced import AsyncReplicateClientEnhanced

# Local imports - Utils
from ..utils.verbose_output import log_stage_emoji
from ..utils.hybrid_progress import HybridVideoProgress, create_hybrid_api_callback
from ..utils.filename_utils import generate_video_filename

# Local imports - Models
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MarkdownJob
from ..models.video_processing import VideoProcessingContext, APIClientConfig

# Local imports - Processing
from .cost_calculator import calculate_cost_from_params
from .input_discovery import discover_markdown_jobs, parse_markdown_job
from .output_generator import save_generation_files
from .profile_loader import load_active_profiles
from .video_downloader import download_video
from .processor import _apply_prompt_modifications


def process_matrix_hybrid(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process video matrix with HYBRID progress (alive-progress + Rich).

    Per manifesto recommendation:
    - alive-progress: Main video generation progress (maximum visual flair)
    - Rich: Detailed sub-operation logging (console output, panels)

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results
    """
    # Setup processing
    async_client, jobs, active_profiles, run_dir = _setup_processing_hybrid(context)

    # Execute with hybrid progress
    results = _execute_video_batch_hybrid(async_client, jobs, active_profiles, run_dir)

    # Return results
    return {
        "total": results["total"],
        "success": results["success"],
        "cost": results["total_cost"],
        "output_dir": run_dir,
        "adjustments": results["adjustments"],
    }


def _setup_processing_hybrid(
    context: ProcessingContext,
) -> Tuple[AsyncReplicateClientEnhanced, List[MarkdownJob], List, Path]:
    """Setup processing environment and discover inputs."""
    # Create async client with WAVES animation
    config = APIClientConfig(api_token=context.client.api_token, poll_interval=3)
    async_client = AsyncReplicateClientEnhanced(config=config)

    # Discover markdown jobs
    log_stage_emoji("preparing", "Discovering markdown jobs...")
    markdown_files = discover_markdown_jobs(context.input_dir)
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]
    logger.success(f"Found {len(jobs)} markdown jobs")

    # Load profiles
    log_stage_emoji("preparing", "Loading video profiles...")
    active_profiles = load_active_profiles(context.profiles_dir)
    logger.success(f"Loaded {len(active_profiles)} profiles")

    # Create output directory
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    if len(active_profiles) == 1:
        profile_suffix = (
            str(active_profiles[0]["name"]).strip().replace("/", "-").replace(" ", "_")
        )
        dir_name = f"{timestamp}_{profile_suffix}"
    else:
        dir_name = f"{timestamp}_VIDEO"
    run_dir = context.output_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Output: {run_dir}")

    return async_client, jobs, active_profiles, run_dir


def _execute_video_batch_hybrid(
    async_client: AsyncReplicateClientEnhanced,
    jobs: List[MarkdownJob],
    active_profiles: List,
    run_dir: Path,
) -> Dict[str, Any]:
    """
    Execute batch with HYBRID progress (alive-progress main + Rich details).

    This follows the manifesto recommendation:
    - alive-progress handles the main visual progress bar with dual-line status
    - Rich handles detailed console logging with colors and formatting
    """
    total = len(jobs) * len(active_profiles)

    # Create hybrid progress (alive-progress + Rich)
    hybrid = HybridVideoProgress()

    success_count = 0
    total_cost = 0.0
    all_adjustments = []

    # Main progress bar using alive-progress (maximum visual appeal!)
    with hybrid.track_generation(total, title="Video Generation Matrix") as (
        bar,
        console,
    ):
        for job in jobs:
            for profile in active_profiles:
                video_name = f"{job.markdown_file.stem}_X_{profile['name']}"

                try:
                    # Update main status (dual-line display below bar)
                    hybrid.update_video_status(
                        video_name, "Initializing", "Setting up video context"
                    )

                    # Create processing context
                    video_context = VideoProcessingContext(
                        client=async_client,
                        prompt_file=job.markdown_file,
                        image_url_file=job.markdown_file,
                        num_frames_file=job.markdown_file,
                        profile=profile,
                        run_dir=run_dir,
                        progress=None,  # Not using Rich Progress
                        task_id=0,  # Not needed for hybrid
                    )

                    # Process single video with hybrid progress
                    video_cost, adjustment_info = _process_video_hybrid(
                        video_context, job, hybrid, video_name
                    )

                    success_count += 1
                    total_cost += video_cost

                    # Track adjustments
                    if adjustment_info and adjustment_info.get("reason"):
                        all_adjustments.append(
                            {
                                "prompt_file": job.markdown_file.name,
                                "profile": profile["name"],
                                **adjustment_info,
                            }
                        )

                    # Mark success (auto-advances bar)
                    hybrid.mark_success(video_name, video_cost)

                except Exception as e:
                    # Mark error with hybrid progress
                    hybrid.mark_error(video_name, str(e))
                    logger.exception(e)
                    raise  # Fail fast

        # Print summary using Rich formatting
        hybrid.print_summary(total, success_count, total_cost)

    return {
        "success": success_count,
        "total": total,
        "total_cost": total_cost,
        "adjustments": all_adjustments,
    }


def _process_video_hybrid(
    context: VideoProcessingContext,
    job: MarkdownJob,
    hybrid: HybridVideoProgress,
    video_name: str,
) -> Tuple[float, Dict[str, Any]]:
    """Process single video with hybrid progress feedback."""

    # Extract data from job
    hybrid.log_phase_start("Preparing", f"Loading inputs for {job.markdown_file.stem}")
    prompt = job.prompt
    image_url = job.image_url
    num_frames = job.num_frames

    # Apply prompt modifications (prefix/suffix) if configured
    prompt = _apply_prompt_modifications(prompt, context.profile)

    # Create output directory
    video_dir = context.run_dir / video_name
    video_dir.mkdir(exist_ok=True)

    # Prepare parameters
    from .processor import _prepare_generation_params

    hybrid.update_video_status(video_name, "Preparing", "Building API parameters")
    params, adjustment_info = _prepare_generation_params(context.profile, num_frames)

    # Log generation details with Rich
    logger.info("═" * 60)
    hybrid.log_phase_start("Generating", f"Model: {context.profile['model_id']}")
    logger.info(f"📝 Prompt: {prompt[:80]}...")
    logger.info(f"🖼️  Image: {image_url[:80]}...")
    logger.info(
        f"⏱️  Duration: {params.get('duration', params.get('num_frames', 'N/A'))}"
    )
    logger.info("═" * 60)

    # Update status for API call
    hybrid.update_video_status(video_name, "Generating", "Sending API request")

    # Create API callback using hybrid progress
    progress_callback = create_hybrid_api_callback(hybrid)

    # Generate video with polling
    video_url = context.client.generate_video_with_polling(
        model_name=context.profile["model_id"],
        image_url=image_url,
        prompt=prompt,
        params=params,
        progress_callback=progress_callback,
        image_url_param=context.profile.get("image_url_param", "image"),
    )

    if not video_url:
        raise Exception(f"No video URL returned from API for {video_name}")

    # Download video
    hybrid.update_video_status(video_name, "Downloading", "Fetching generated video")
    hybrid.log_phase_start("Downloading", f"URL: {video_url[:60]}...")

    video_filename = generate_video_filename(job.markdown_file.name)
    video_path = video_dir / video_filename
    download_video(video_url, video_path)

    # Calculate cost
    video_cost = calculate_cost_from_params(context.profile, params, num_frames)

    # Save documentation
    hybrid.update_video_status(video_name, "Finalizing", "Saving documentation")
    hybrid.log_phase_start("Finalizing", "Generating reports and logs")

    gen_context = GenerationContext(
        prompt_file=job.markdown_file,
        image_url_file=job.markdown_file,
        num_frames_file=job.markdown_file,
        output_dir=video_dir,
        prompt=prompt,
        image_url=image_url,
        num_frames=num_frames,
        profile=context.profile,
        params=params,
        video_url=video_url,
        video_path=video_path,
        cost=video_cost,
        adjustment_info=adjustment_info,
    )
    save_generation_files(gen_context)

    return video_cost, adjustment_info
