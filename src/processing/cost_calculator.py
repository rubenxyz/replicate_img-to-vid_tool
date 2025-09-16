"""Video generation cost calculation - supports multiple pricing models."""
from typing import Dict, Any, Union

# Constants
ESTIMATED_SECONDS_PER_FRAME = 3  # Rough estimate for time-based pricing


def _validate_numeric_field(value: Union[int, float], field_name: str, profile_name: str) -> None:
    """
    Validate that a numeric field is valid.
    
    Args:
        value: The value to validate
        field_name: Name of the field being validated
        profile_name: Name of the profile for error messages
        
    Raises:
        ValueError: If value is not a valid positive number
    """
    if not isinstance(value, (int, float)) or value < 0:
        raise ValueError(
            f"Profile '{profile_name}' has invalid {field_name}: {value}"
        )


def calculate_video_cost(profile: Dict[str, Any], num_frames: int) -> float:
    """
    Calculate cost for video generation based on pricing model.
    
    Supports:
    - Frame-based: cost_per_frame × number_of_frames
    - Prediction-based: fixed cost_per_prediction
    - Time-based: cost_per_second × estimated_seconds
    
    Args:
        profile: Profile dictionary containing pricing configuration
        num_frames: Number of frames for the video
        
    Returns:
        Cost in USD based on pricing model
        
    Raises:
        ValueError: If pricing configuration is missing or invalid
    """
    if 'pricing' not in profile:
        raise ValueError(f"Profile '{profile.get('name', 'unknown')}' missing pricing configuration")
    
    pricing = profile['pricing']
    
    # Frame-based pricing model
    if 'cost_per_frame' in pricing:
        cost_per_frame = pricing['cost_per_frame']
        _validate_numeric_field(cost_per_frame, 'cost_per_frame', profile.get('name', 'unknown'))
        
        # Calculate total cost: frames × cost_per_frame
        total_cost = cost_per_frame * num_frames
        return round(total_cost, 4)
    
    # Prediction-based pricing (Replicate model)
    elif 'cost_per_prediction' in pricing:
        cost_per_prediction = pricing['cost_per_prediction']
        _validate_numeric_field(cost_per_prediction, 'cost_per_prediction', profile.get('name', 'unknown'))
        
        # Fixed cost per generation
        return round(cost_per_prediction, 4)
    
    # Time-based pricing (Replicate compute time)
    elif 'cost_per_second' in pricing:
        cost_per_second = pricing['cost_per_second']
        _validate_numeric_field(cost_per_second, 'cost_per_second', profile.get('name', 'unknown'))
        
        # Estimate compute time based on frames
        estimated_seconds = num_frames * ESTIMATED_SECONDS_PER_FRAME
        total_cost = cost_per_second * estimated_seconds
        return round(total_cost, 4)
    
    else:
        raise ValueError(
            f"Profile '{profile.get('name', 'unknown')}' must have one of: "
            f"'cost_per_frame', 'cost_per_prediction', or 'cost_per_second' in pricing section"
        )