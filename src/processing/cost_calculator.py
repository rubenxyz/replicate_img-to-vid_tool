"""Video generation cost calculation - supports multiple pricing models."""

from typing import Dict, Any, Union


def _validate_numeric_field(
    value: Union[int, float], field_name: str, profile_name: str
) -> None:
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
        raise ValueError(f"Profile '{profile_name}' has invalid {field_name}: {value}")


def calculate_cost_from_params(
    profile: Dict[str, Any], params: Dict[str, Any], num_frames: int
) -> float:
    """
    Calculate video cost from generation parameters with duration conversion.

    Handles duration type conversion (frames to seconds) internally.

    Args:
        profile: Profile configuration with duration_config
        params: Generation parameters containing duration value
        num_frames: Fallback frame count

    Returns:
        Cost in dollars
    """
    param_name = profile["duration_config"]["duration_param_name"]
    video_duration = params.get(param_name, num_frames)

    # Convert to seconds if needed
    if profile["duration_config"]["duration_type"] == "frames":
        fps = profile["duration_config"]["fps"]
        video_duration_seconds = int(video_duration / fps)
    else:
        video_duration_seconds = video_duration

    return calculate_video_cost(profile, video_duration_seconds)


def calculate_video_cost(profile: Dict[str, Any], video_duration_seconds: int) -> float:
    """
    Calculate cost for video generation based on Replicate compute-time pricing.

    For video generation, cost = cost_per_second × video_duration_seconds
    (The duration is the length of the output video, not compute time)

    Args:
        profile: Profile dictionary containing pricing configuration
        video_duration_seconds: Duration of the generated video in seconds

    Returns:
        Cost in USD based on video duration

    Raises:
        ValueError: If pricing configuration is missing or invalid
    """
    if "pricing" not in profile:
        raise ValueError(
            f"Profile '{profile.get('name', 'unknown')}' missing pricing configuration"
        )

    pricing = profile["pricing"]

    # Video generation pricing (cost per second of video output)
    if "cost_per_second" in pricing:
        cost_per_second = pricing["cost_per_second"]
        _validate_numeric_field(
            cost_per_second, "cost_per_second", profile.get("name", "unknown")
        )

        # Calculate cost: video_duration × cost_per_second
        total_cost = cost_per_second * video_duration_seconds
        return round(total_cost, 4)

    else:
        raise ValueError(
            f"Profile '{profile.get('name', 'unknown')}' must have 'cost_per_second' in pricing section"
        )
