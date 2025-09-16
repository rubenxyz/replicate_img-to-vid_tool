"""Enhanced processor with verbose terminal output."""
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import threading
from loguru import logger

from ..api.async_client import AsyncReplicateClient, PollingThread
from ..utils.verbose_output import VerboseContext, log_stage_emoji, create_progress_display
from .input_discovery import discover_input_triplets, load_input_data
from .profile_loader import load_active_profiles
from .cost_calculator import calculate_video_cost
from .video_downloader import download_video
from .output_generator import save_generation_files
from .duration_handler import process_duration, get_duration_parameter_name, should_include_fps
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from .generation_logger import log_generation_complete


def process_matrix_verbose(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process video matrix with verbose terminal output.
    
    Args:
        context: ProcessingContext with all required paths and client
        
    Returns:
        Dictionary with processing results
    """
    with VerboseContext() as verbose:
        # Create async client for polling
        async_client = AsyncReplicateClient(
            api_token=context.client.api_token,
            poll_interval=3
        )
        
        # Discover inputs
        log_stage_emoji("preparing", "Discovering input triplets...")
        triplets = discover_input_triplets(
            context.prompt_dir, context.image_url_dir, context.num_frames_dir
        )
        logger.success(f"Found {len(triplets)} input triplets")
        
        # Load profiles
        log_stage_emoji("preparing", "Loading video profiles...")
        active_profiles = load_active_profiles(context.profiles_dir)
        logger.success(f"Loaded {len(active_profiles)} profiles")
        
        # Create output directory
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        run_dir = context.output_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Output: {run_dir}")
        
        # Process with enhanced progress
        total = len(triplets) * len(active_profiles)
        progress = create_progress_display()
        
        # Start progress tracking
        main_task = progress.add_task(
            f"Processing {total} videos",
            total=total,
            status="Starting..."
        )
        
        success_count = 0
        total_cost = 0.0
        all_adjustments = []
        
        with progress:
            for idx, (prompt_file, image_url_file, num_frames_file) in enumerate(triplets):
                for profile in active_profiles:
                    # Update progress
                    video_name = f"{prompt_file.stem}_X_{profile['name']}"
                    progress.update(
                        main_task,
                        description=f"[cyan]{video_name}",
                        status="Processing..."
                    )
                    
                    try:
                        # Process single video with verbose output
                        video_cost, adjustment_info = _process_video_verbose(
                            async_client, prompt_file, image_url_file, 
                            num_frames_file, profile, run_dir, progress, main_task
                        )
                        
                        success_count += 1
                        total_cost += video_cost
                        
                        # Track adjustments
                        if adjustment_info and adjustment_info.get('reason'):
                            all_adjustments.append({
                                'prompt_file': prompt_file.name,
                                'profile': profile['name'],
                                **adjustment_info
                            })
                            
                        # Update progress
                        progress.advance(main_task)
                        progress.update(
                            main_task,
                            status=f"✅ Complete (${video_cost:.2f})"
                        )
                        
                    except Exception as e:
                        log_stage_emoji("failed", f"Failed: {video_name}")
                        logger.exception(e)
                        progress.update(main_task, status="❌ Failed")
                        raise  # Fail fast
                        
        # Final summary
        logger.success(f"🎉 Completed {success_count}/{total} videos")
        logger.info(f"💰 Total cost: ${total_cost:.2f}")
        
        return {
            "total": total,
            "success": success_count,
            "failed": total - success_count,
            "cost": total_cost,
            "output_dir": run_dir,
            "adjustments": all_adjustments
        }


def _process_video_verbose(
    client: AsyncReplicateClient,
    prompt_file: Path,
    image_url_file: Path,
    num_frames_file: Path,
    profile: Dict[str, Any],
    run_dir: Path,
    progress: Any,
    task_id: int
) -> Tuple[float, Dict[str, Any]]:
    """Process single video with verbose output and polling."""
    
    # Load inputs
    log_stage_emoji("preparing", f"Loading inputs for {prompt_file.stem}")
    prompt, image_url, num_frames = load_input_data(
        prompt_file, image_url_file, num_frames_file
    )
    
    # Create output directory
    video_name = f"{prompt_file.stem}_X_{profile['name']}"
    video_dir = run_dir / video_name
    video_dir.mkdir(exist_ok=True)
    
    # Prepare parameters
    params, adjustment_info = _prepare_params_verbose(profile, num_frames)
    
    # Log generation details
    logger.info("═" * 60)
    log_stage_emoji("starting", f"Generating: {video_name}")
    logger.info(f"📝 Prompt: {prompt[:80]}...")
    logger.info(f"🖼️  Image: {image_url[:80]}...")
    logger.info(f"⚙️  Model: {profile['model_id']}")
    logger.info(f"⏱️  Duration: {params.get('duration', params.get('num_frames', 'N/A'))}")
    logger.info("═" * 60)
    
    # Generate with polling
    def progress_callback(status: str, percentage: Optional[float]):
        """Update progress bar with status."""
        if percentage is not None:
            progress.update(
                task_id,
                status=f"⚙️ {status.title()} ({percentage:.0f}%)"
            )
        else:
            progress.update(task_id, status=f"⏳ {status.title()}")
    
    video_url = client.generate_video_with_polling(
        model_name=profile['model_id'],
        image_url=image_url,
        prompt=prompt,
        params=params,
        progress_callback=progress_callback
    )
    
    if not video_url:
        raise Exception("No video URL returned from API")
    
    # Download video
    log_stage_emoji("downloading", f"Downloading video...")
    video_path = video_dir / f"{prompt_file.stem}.mp4"
    download_video(video_url, video_path)
    
    # Calculate cost
    video_cost = calculate_video_cost(profile, num_frames)
    
    # Save documentation
    log_stage_emoji("saving", "Saving generation files...")
    context = GenerationContext(
        prompt_file=prompt_file,
        image_url_file=image_url_file,
        num_frames_file=num_frames_file,
        output_dir=video_dir,
        prompt=prompt,
        image_url=image_url,
        num_frames=num_frames,
        profile=profile,
        params=params,
        video_url=video_url,
        video_path=video_path,
        cost=video_cost,
        adjustment_info=adjustment_info
    )
    save_generation_files(context)
    
    log_stage_emoji("complete", f"Completed: {video_path.name} (${video_cost:.2f})")
    
    return video_cost, adjustment_info


def _prepare_params_verbose(profile: Dict[str, Any], num_frames: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Prepare parameters with verbose logging of adjustments."""
    params = profile['parameters'].copy()
    
    # Process duration
    adjusted_duration, was_adjusted, adjustment_info = process_duration(num_frames, profile)
    
    if was_adjusted:
        logger.warning(f"⚠️ Duration adjusted: {adjustment_info['reason']}")
        logger.info(f"  Original: {adjustment_info['original_value']}")
        logger.info(f"  Adjusted: {adjustment_info['adjusted_value']}")
    
    # Set duration parameter
    param_name = get_duration_parameter_name(profile)
    params[param_name] = adjusted_duration
    
    # Include fps if needed
    if should_include_fps(profile):
        params['fps'] = profile['duration_config']['fps']
    
    return params, adjustment_info