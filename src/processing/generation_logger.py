"""Generation logging utilities."""
from pathlib import Path
from typing import Dict, Any
from loguru import logger


def log_generation_start(subfolder_name: str, profile: Dict[str, Any],
                        prompt: str, image_url: str, num_frames: int,
                        params: Dict[str, Any]) -> None:
    """
    Log the start of video generation.
    
    Args:
        subfolder_name: Name of the output subfolder
        profile: Profile configuration dictionary
        prompt: Generation prompt text
        image_url: Source image URL
        num_frames: Number of frames to generate
        params: Generation parameters
    """
    logger.info(f"═══════════════════════════════════════════════════════")
    logger.info(f"GENERATING VIDEO: {subfolder_name}")
    logger.info(f"═══════════════════════════════════════════════════════")
    logger.info(f"Profile: {profile['name']}")
    logger.info(f"Model: {profile['model_id']}")
    logger.info(f"Prompt: {prompt[:100]}...")
    logger.info(f"Image URL: {image_url[:80]}...")
    logger.info(f"Frames: {num_frames}")
    logger.debug(f"Full parameters: {params}")


def log_generation_complete(video_path: Path, video_cost: float) -> None:
    """
    Log the completion of video generation.
    
    Args:
        video_path: Path to the generated video file
        video_cost: Cost of the video generation in USD
    """
    logger.info(f"💰 Video cost: ${video_cost:.2f}")
    logger.success(f"✅ Video saved: {video_path}")
    logger.info(f"═══════════════════════════════════════════════════════")