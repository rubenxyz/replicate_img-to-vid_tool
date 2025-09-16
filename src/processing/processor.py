"""Video generation processor with matrix handling."""
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from loguru import logger
from rich.progress import Progress

from ..api.client import ReplicateClient
from .input_discovery import discover_input_triplets, load_input_data
from .profile_loader import load_active_profiles
from .cost_calculator import calculate_video_cost
from .video_downloader import download_video
from .output_generator import save_generation_files
from .duration_handler import process_duration, get_duration_parameter_name, should_include_fps
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from .generation_logger import log_generation_start, log_generation_complete


def _create_run_directory(output_dir: Path) -> Path:
    """Create timestamped output directory for this run."""
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {run_dir}")
    return run_dir


def _process_all_videos(client: ReplicateClient, triplets: List[Tuple[Path, Path, Path]],
                       active_profiles: List[Dict[str, Any]], run_dir: Path,
                       progress: Optional[Progress] = None) -> Tuple[int, float, List[Dict[str, Any]]]:
    """Process all video generations in the matrix."""
    total = len(triplets) * len(active_profiles)
    success_count = 0
    total_cost = 0.0
    all_adjustments = []
    
    task_id = None
    if progress:
        task_id = progress.add_task("Generating videos", total=total)
    
    for prompt_file, image_url_file, num_frames_file in triplets:
        for profile in active_profiles:
            # Process single video
            video_cost, adjustment_info = _process_single_video(
                client, prompt_file, image_url_file, num_frames_file,
                profile, run_dir
            )
            
            # Track adjustment if any
            if adjustment_info and adjustment_info.get('reason'):
                adjustment_record = {
                    'prompt_file': prompt_file.name,
                    'profile': profile['name'],
                    **adjustment_info
                }
                all_adjustments.append(adjustment_record)
            
            success_count += 1
            total_cost += video_cost
            
            if progress:
                progress.advance(task_id)
    
    return success_count, total_cost, all_adjustments


def process_matrix(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process prompt-image-frames-profile matrix for video generation.
    
    Args:
        context: ProcessingContext with all required paths and client
        
    Returns:
        Dictionary with processing results
        
    Raises:
        Exception: On any processing failure (fail-fast)
    """
    # 1. Discover input triplets
    triplets = discover_input_triplets(
        context.prompt_dir, context.image_url_dir, context.num_frames_dir
    )
    logger.info(f"Found {len(triplets)} prompt-image-frame triplets")
    
    # 2. Load video profiles
    active_profiles = load_active_profiles(context.profiles_dir)
    logger.info(f"Loaded {len(active_profiles)} video profiles")
    
    # 3. Create timestamped output directory
    run_dir = _create_run_directory(context.output_dir)
    
    # 4. Process matrix sequentially
    total = len(triplets) * len(active_profiles)
    success_count, total_cost, all_adjustments = _process_all_videos(
        context.client, triplets, active_profiles, run_dir, context.progress
    )
    
    return {
        "total": total,
        "success": success_count,
        "failed": total - success_count,
        "cost": total_cost,
        "output_dir": run_dir,
        "adjustments": all_adjustments
    }


def _process_single_video(client: ReplicateClient, prompt_file: Path, image_url_file: Path,
                         num_frames_file: Path, profile: Dict[str, Any],
                         run_dir: Path) -> Tuple[float, Dict[str, Any]]:
    """
    Process a single video generation.
    
    Args:
        client: Replicate API client
        prompt_file: Prompt file path
        image_url_file: Image URL file path
        num_frames_file: Num frames file path
        profile: Profile configuration
        run_dir: Output directory
        
    Returns:
        Tuple of (cost, adjustment_info)
        
    Raises:
        Exception: On generation failure
    """
    # Load input data
    prompt, image_url, num_frames = load_input_data(
        prompt_file, image_url_file, num_frames_file
    )
    
    # Create output directory
    video_dir = _create_video_directory(run_dir, prompt_file, profile)
    subfolder_name = video_dir.name
    
    logger.info(f"Processing: {subfolder_name}")
    
    try:
        # Prepare parameters with duration handling
        params, adjustment_info = _prepare_generation_params(profile, num_frames)
        
        # Log generation start
        log_generation_start(subfolder_name, profile, prompt, image_url, num_frames, params)
        
        # Generate and download video
        video_url, video_path = _generate_and_download_video(
            client, profile, image_url, prompt, params, video_dir, prompt_file
        )
        
        # Calculate cost
        video_cost = calculate_video_cost(profile, num_frames)
        
        # Create generation context with all data
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
        
        # Save all documentation
        save_generation_files(context)
        
        # Log completion
        log_generation_complete(video_path, video_cost)
        
        return video_cost, adjustment_info
        
    except Exception as e:
        logger.error(f"Failed: {prompt_file.name} + {profile['name']}: {e}")
        raise  # Fail-fast philosophy


def _prepare_generation_params(profile: Dict[str, Any], num_frames: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Prepare API parameters with duration handling.
    
    Returns:
        Tuple of (params, adjustment_info)
    """
    params = profile['parameters'].copy()
    
    # Process duration based on profile configuration
    adjusted_duration, was_adjusted, adjustment_info = process_duration(num_frames, profile)
    
    # Get the correct parameter name from profile
    param_name = get_duration_parameter_name(profile)
    params[param_name] = adjusted_duration
    
    # Include fps if needed by the model
    if should_include_fps(profile):
        params['fps'] = profile['duration_config']['fps']
    
    return params, adjustment_info


def _create_video_directory(run_dir: Path, prompt_file: Path, profile: Dict[str, Any]) -> Path:
    """Create output directory for video generation."""
    subfolder_name = f"{prompt_file.stem}_X_{profile['name']}"
    video_dir = run_dir / subfolder_name
    video_dir.mkdir(exist_ok=True)
    return video_dir


def _generate_and_download_video(client: ReplicateClient, profile: Dict[str, Any],
                                image_url: str, prompt: str, params: Dict[str, Any],
                                video_dir: Path, prompt_file: Path) -> Tuple[str, Path]:
    """Generate video via API and download it."""
    # Generate video
    video_url = client.generate_video(
        model_name=profile['model_id'],
        image_url=image_url,
        prompt=prompt,
        params=params
    )
    
    if not video_url:
        raise Exception("No video URL returned from API")
    
    # Download and save video with prompt filename
    video_path = video_dir / f"{prompt_file.stem}.mp4"
    logger.info(f"Downloading video from: {video_url[:100]}...")
    download_video(video_url, video_path)
    
    return video_url, video_path