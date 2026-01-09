"""Enhanced processor with verbose terminal output."""

# Standard library imports
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Third-party imports
from loguru import logger

# Local imports - API
from ..api.async_client_enhanced import AsyncReplicateClientEnhanced

# Local imports - Utils
from ..utils.verbose_output import VerboseContext, log_stage_emoji
from ..utils.epic_progress import VideoGenerationProgress, create_api_callback
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


def process_matrix_verbose(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process video matrix with verbose terminal output.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results
    """
    with VerboseContext() as verbose:
        # Setup processing
        async_client, jobs, active_profiles, run_dir = _setup_processing(context)

        # Execute video batch
        results = _execute_video_batch(async_client, jobs, active_profiles, run_dir)

        # Generate summary
        return _generate_summary(results, run_dir)


def _setup_processing(
    context: ProcessingContext,
) -> Tuple[AsyncReplicateClientEnhanced, List[MarkdownJob], List, Path]:
    """Setup processing environment and discover inputs."""
    # Create enhanced async client with alive-progress animation
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
        # Sanitize profile name for filesystem
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


def _execute_video_batch(
    async_client: AsyncReplicateClientEnhanced,
    jobs: List[MarkdownJob],
    active_profiles: List,
    run_dir: Path,
) -> Dict[str, Any]:
    """Execute batch video processing with epic progress tracking."""
    total = len(jobs) * len(active_profiles)

    # Create epic progress bar
    epic_progress = VideoGenerationProgress()

    success_count = 0
    total_cost = 0.0
    all_adjustments = []

    # Use epic progress with panel wrapper
    with epic_progress.track_generation(total, title="Video Generation Matrix") as (
        progress,
        main_task,
    ):
        for job in jobs:
            for profile in active_profiles:
                video_name = f"{job.markdown_file.stem}_X_{profile['name']}"

                try:
                    # Update progress with video name and phase
                    epic_progress.update_status(
                        progress,
                        main_task,
                        status="Starting...",
                        video_name=video_name,
                        phase="Initializing",
                    )

                    # Create processing context
                    video_context = VideoProcessingContext(
                        client=async_client,
                        prompt_file=job.markdown_file,
                        image_url_file=job.markdown_file,
                        num_frames_file=job.markdown_file,
                        profile=profile,
                        run_dir=run_dir,
                        progress=progress,
                        task_id=main_task,
                    )

                    # Process single video with epic progress
                    video_cost, adjustment_info = _process_video_verbose(
                        video_context, job, epic_progress
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

                    # Mark as successful with cost
                    epic_progress.mark_success(
                        progress, main_task, video_name, video_cost
                    )

                    # Advance progress
                    progress.advance(main_task)

                    # Update total cost in status
                    epic_progress.update_with_cost(
                        progress,
                        main_task,
                        status="Complete",
                        total_cost=total_cost,
                        video_name=video_name,
                    )

                except Exception as e:
                    # Mark error with epic progress
                    epic_progress.mark_error(progress, main_task, video_name, str(e))
                    logger.exception(e)
                    raise  # Fail fast

    return {
        "success_count": success_count,
        "total": total,
        "total_cost": total_cost,
        "adjustments": all_adjustments,
    }


def _generate_summary(results: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
    """Generate final processing summary."""
    total = results["total"]
    success_count = results["success_count"]
    total_cost = results["total_cost"]

    # Final summary
    logger.success(f"🎉 Completed {success_count}/{total} videos")
    logger.info(f"💰 Total cost: ${total_cost:.2f}")

    return {
        "total": total,
        "success": success_count,
        "cost": total_cost,
        "output_dir": run_dir,
        "adjustments": results["adjustments"],
    }


def _process_video_verbose(
    context: VideoProcessingContext,
    job: MarkdownJob,
    epic_progress: VideoGenerationProgress,
) -> Tuple[float, Dict[str, Any]]:
    """Process single video with verbose output and polling."""

    # Extract data from job
    log_stage_emoji("preparing", f"Loading inputs for {job.markdown_file.stem}")
    prompt = job.prompt
    image_url = job.image_url
    num_frames = job.num_frames

    # Apply prompt modifications (prefix/suffix) if configured
    prompt = _apply_prompt_modifications(prompt, context.profile)

    # Create output directory
    video_name = f"{job.markdown_file.stem}_X_{context.profile['name']}"
    video_dir = context.run_dir / video_name
    video_dir.mkdir(exist_ok=True)

    # Prepare parameters
    params, adjustment_info = _prepare_params_verbose(context.profile, num_frames)

    # Update progress: preparing phase
    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Preparing API call",
        video_name=video_name,
        phase="Preparing",
    )

    # Log generation details
    logger.info("═" * 60)
    log_stage_emoji("starting", f"Generating: {video_name}")
    logger.info(f"📝 Prompt: {prompt[:80]}...")
    logger.info(f"🖼️  Image: {image_url[:80]}...")
    logger.info(f"⚙️  Model: {context.profile['model_id']}")
    logger.info(
        f"⏱️  Duration: {params.get('duration', params.get('num_frames', 'N/A'))}"
    )
    logger.info("═" * 60)

    # Create API callback using epic progress helper
    progress_callback = create_api_callback(
        context.progress, context.task_id, epic_progress.console
    )

    video_url = context.client.generate_video_with_polling(
        model_name=context.profile["model_id"],
        image_url=image_url,
        prompt=prompt,
        params=params,
        progress_callback=progress_callback,
        image_url_param=context.profile.get("image_url_param", "image"),
    )

    if not video_url:
        error_msg = f"No video URL returned from API for {video_name}"
        logger.error(error_msg)
        raise Exception(error_msg)

    # Update progress: downloading phase
    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Downloading video",
        video_name=video_name,
        phase="Downloading",
    )

    video_filename = generate_video_filename(job.markdown_file.name)
    video_path = video_dir / video_filename
    download_video(video_url, video_path)

    # Calculate cost based on actual video duration
    video_cost = calculate_cost_from_params(context.profile, params, num_frames)

    # Update progress: saving phase
    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Saving documentation",
        video_name=video_name,
        phase="Finalizing",
    )

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

    log_stage_emoji("complete", f"Completed: {video_path.name} (${video_cost:.2f})")

    return video_cost, adjustment_info


def _prepare_params_verbose(
    profile: Dict[str, Any], num_frames: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Prepare parameters with verbose logging of adjustments."""
    # Reuse logic from processor module
    from .processor import _prepare_generation_params

    params, adjustment_info = _prepare_generation_params(profile, num_frames)

    # Add verbose logging for adjustments
    if adjustment_info and adjustment_info.get("reason"):
        logger.warning(f"⚠️ Duration adjusted: {adjustment_info['reason']}")
        # Handle different adjustment_info structures for frames vs seconds
        if adjustment_info.get("type") == "seconds":
            logger.info(
                f"  Original: {adjustment_info['original_seconds']}s ({adjustment_info['original_frames']} frames)"
            )
            logger.info(f"  Adjusted: {adjustment_info['adjusted_seconds']}s")
        else:  # frames type
            logger.info(f"  Original: {adjustment_info['original']} frames")
            logger.info(f"  Adjusted: {adjustment_info['adjusted']} frames")

    return params, adjustment_info
