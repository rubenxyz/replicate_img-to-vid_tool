"""Duration handling for frame-based and seconds-based video generation."""
import math
from typing import Dict, Any, Tuple
from loguru import logger


def process_duration(frame_count: int, profile: Dict[str, Any]) -> Tuple[Any, bool, Dict[str, Any]]:
    """
    Process duration based on profile configuration.
    
    Args:
        frame_count: Original frame count from input file
        profile: Profile dictionary with duration_config
        
    Returns:
        Tuple of (adjusted_value, was_adjusted, adjustment_info)
        adjustment_info contains: original, adjusted, reason
    """
    duration_config = profile['duration_config']
    duration_type = duration_config['duration_type']
    fps = duration_config['fps']
    duration_min = duration_config['duration_min']
    duration_max = duration_config['duration_max']
    
    if duration_type == 'frames':
        return _process_frame_duration(frame_count, duration_min, duration_max)
    elif duration_type == 'seconds':
        return _process_seconds_duration(frame_count, fps, duration_min, duration_max)
    else:
        raise ValueError(f"Invalid duration_type: {duration_type}")


def _process_frame_duration(frame_count: int, min_frames: int, max_frames: int) -> Tuple[int, bool, Dict[str, Any]]:
    """
    Process frame-based duration with min/max constraints.
    
    Args:
        frame_count: Original frame count
        min_frames: Minimum allowed frames
        max_frames: Maximum allowed frames
        
    Returns:
        Tuple of (adjusted_frames, was_adjusted, adjustment_info)
    """
    original = frame_count
    adjusted = frame_count
    was_adjusted = False
    reason = None
    
    if frame_count < min_frames:
        adjusted = min_frames
        was_adjusted = True
        reason = f"Below minimum ({min_frames})"
        logger.warning(f"Frame count {original} below minimum, adjusted to {adjusted}")
    elif frame_count > max_frames:
        adjusted = max_frames
        was_adjusted = True
        reason = f"Exceeded maximum ({max_frames})"
        logger.warning(f"Frame count {original} exceeds maximum, adjusted to {adjusted}")
    
    adjustment_info = {
        'original': original,
        'adjusted': adjusted,
        'reason': reason,
        'type': 'frames'
    }
    
    return adjusted, was_adjusted, adjustment_info


def _process_seconds_duration(frame_count: int, fps: int, min_seconds: int, max_seconds: int) -> Tuple[int, bool, Dict[str, Any]]:
    """
    Process seconds-based duration with frame-to-second conversion.
    
    Args:
        frame_count: Original frame count
        fps: Frames per second for conversion
        min_seconds: Minimum allowed seconds
        max_seconds: Maximum allowed seconds
        
    Returns:
        Tuple of (adjusted_seconds, was_adjusted, adjustment_info)
    """
    # Convert frames to seconds, always round up
    original_seconds = math.ceil(frame_count / fps)
    adjusted_seconds = original_seconds
    was_adjusted = False
    reason = None
    
    if original_seconds < min_seconds:
        adjusted_seconds = min_seconds
        was_adjusted = True
        reason = f"Below minimum ({min_seconds} seconds)"
        logger.warning(f"Duration {original_seconds}s below minimum, adjusted to {adjusted_seconds}s")
    elif original_seconds > max_seconds:
        adjusted_seconds = max_seconds
        was_adjusted = True
        reason = f"Exceeded maximum ({max_seconds} seconds)"
        logger.warning(f"Duration {original_seconds}s exceeds maximum, adjusted to {adjusted_seconds}s")
    
    adjustment_info = {
        'original_frames': frame_count,
        'original_seconds': original_seconds,
        'adjusted_seconds': adjusted_seconds,
        'fps': fps,
        'reason': reason,
        'type': 'seconds'
    }
    
    return adjusted_seconds, was_adjusted, adjustment_info


def get_duration_parameter_name(profile: Dict[str, Any]) -> str:
    """
    Get the parameter name to use for duration in the API call.
    
    Args:
        profile: Profile dictionary with duration_config
        
    Returns:
        Parameter name string (e.g., 'num_frames', 'duration', 'seconds')
    """
    return profile['duration_config']['duration_param_name']


def should_include_fps(profile: Dict[str, Any]) -> bool:
    """
    Check if fps should be included in API parameters.
    
    Some models require fps even for frame-based generation.
    This is determined by whether 'fps' exists in the params section.
    
    Args:
        profile: Profile dictionary
        
    Returns:
        True if fps should be included in API call
    """
    # Check if fps is mentioned in the original params
    # If it was there before, keep it
    return 'fps' in profile.get('parameters', {})