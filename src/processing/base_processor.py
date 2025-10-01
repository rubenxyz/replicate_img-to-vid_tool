"""Base processor class with shared functionality."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple

from .duration_handler import process_duration, get_duration_parameter_name, should_include_fps


class BaseVideoProcessor(ABC):
    """Base class for video processing with shared logic."""
    
    @abstractmethod
    def process_video(self, *args, **kwargs) -> Tuple[float, Dict[str, Any]]:
        """Process a single video. Must be implemented by subclasses."""
        pass
    
    def prepare_generation_params(self, profile: Dict[str, Any], num_frames: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Prepare API parameters with duration handling.
        
        Args:
            profile: Profile configuration
            num_frames: Number of frames
            
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
    
    def create_video_directory(self, run_dir: Path, prompt_file: Path, profile: Dict[str, Any]) -> Path:
        """
        Create output directory for video generation.
        
        Args:
            run_dir: Base output directory
            prompt_file: Prompt file for naming
            profile: Profile configuration
            
        Returns:
            Path to created video directory
        """
        subfolder_name = f"{prompt_file.stem}_X_{profile['name']}"
        video_dir = run_dir / subfolder_name
        video_dir.mkdir(exist_ok=True)
        return video_dir