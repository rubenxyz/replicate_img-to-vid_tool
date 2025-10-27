#!/usr/bin/env python
"""Standalone cost estimation script - calculates costs without generating videos."""
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from src.processing.input_discovery import discover_input_triplets
from src.processing.profile_loader import load_active_profiles
from src.processing.cost_calculator import calculate_video_cost
from src.processing.duration_handler import process_duration
from src.config.settings import PROMPT_DIR, IMAGE_URL_DIR, NUM_FRAMES_DIR, PROFILES_DIR, OUTPUT_DIR
from loguru import logger


def load_estimation_data() -> Tuple[List[Any], List[Tuple[Path, Path, Path]]]:
    """
    Load profiles and discover input triplets.
    
    Returns:
        Tuple of (profiles, triplets)
        
    Raises:
        Exception: If loading fails
    """
    # Load profiles
    profiles = load_active_profiles(PROFILES_DIR)
    logger.info(f"Loaded {len(profiles)} profiles")
    
    # Discover input triplets
    triplets = discover_input_triplets(PROMPT_DIR, IMAGE_URL_DIR, NUM_FRAMES_DIR)
    logger.info(f"Found {len(triplets)} input triplets")
    
    return profiles, triplets


def calculate_all_costs(profiles: List[Dict[str, Any]], triplets: List[Tuple[Path, Path, Path]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Calculate costs for all profiles and video durations.
    
    Args:
        profiles: List of profile dictionaries
        triplets: List of input file triplets
        
    Returns:
        Tuple of (cost_data, duration_list, profile_totals)
        profile_totals is a dict of {profile_name: total_seconds}
    """
    # Read frame counts from input files
    frame_data = []
    
    for prompt_file, _, num_frames_file in triplets:
        try:
            num_frames_str = num_frames_file.read_text().strip()
            num_frames = int(num_frames_str)
            frame_data.append({
                'prompt': prompt_file.stem,
                'frames': num_frames
            })
            logger.info(f"{prompt_file.stem}: {num_frames} frames")
        except Exception as e:
            logger.error(f"Failed to read frames from {num_frames_file}: {e}")
            continue
    
    # Calculate costs for each profile
    cost_data = []
    profile_totals = {}  # Track total seconds per profile
    
    for profile in profiles:
        try:
            # Process each video's duration using profile's rules
            profile_total_seconds = 0
            duration_list = []
            
            for item in frame_data:
                # Convert frames to seconds and apply min/max limits
                adjusted_duration, was_adjusted, adjustment_info = process_duration(
                    item['frames'], profile
                )
                
                # Get the actual duration in seconds
                if profile['duration_config']['duration_type'] == 'frames':
                    # Convert frames to seconds
                    fps = profile['duration_config']['fps']
                    duration_seconds = int(adjusted_duration / fps)
                else:  # already in seconds
                    duration_seconds = adjusted_duration
                
                profile_total_seconds += duration_seconds
                duration_list.append({
                    'prompt': item['prompt'],
                    'frames': item['frames'],
                    'duration': duration_seconds,
                    'adjusted': was_adjusted
                })
            
            # Calculate total cost for this profile
            total_cost = calculate_video_cost(profile, profile_total_seconds)
            cost_per_video = total_cost / len(triplets) if triplets else 0
            
            # Get pricing info
            pricing = profile.get('pricing', {})
            cost_per_second = pricing.get('cost_per_second', 0)
            
            cost_data.append({
                'profile': profile['name'],
                'model': profile['model_id'],
                'cost_per_second': cost_per_second,
                'total_seconds': profile_total_seconds,
                'total_cost': total_cost,
                'cost_per_video': cost_per_video,
                'num_videos': len(triplets),
                'duration_list': duration_list
            })
            
            profile_totals[profile['name']] = profile_total_seconds
            
            logger.info(f"Profile '{profile['name']}': ${total_cost:.4f} for {profile_total_seconds}s total video")
        except Exception as e:
            logger.error(f"Failed to calculate cost for profile {profile['name']}: {e}")
    
    # Use the first profile's duration list for the report (they should be similar)
    display_duration_list = cost_data[0]['duration_list'] if cost_data else []
    
    return cost_data, display_duration_list, profile_totals


def generate_cost_report(cost_data: List[Dict[str, Any]], duration_list: List[Dict[str, Any]], 
                         profile_totals: Dict[str, int], num_triplets: int) -> Path:
    """
    Generate markdown cost estimation report.
    
    Args:
        cost_data: List of cost calculations per profile
        duration_list: List of video durations (from first profile)
        profile_totals: Dict of total seconds per profile
        num_triplets: Number of input triplets
        
    Returns:
        Path to generated report
    """
    # Create output directory with timestamp; use active profile as suffix when single profile is active
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    if len(cost_data) == 1:
        # Sanitize profile name for filesystem
        profile_suffix = str(cost_data[0]['profile']).strip().replace('/', '-').replace(' ', '_')
        dir_name = f"{timestamp}_{profile_suffix}"
    else:
        dir_name = f"{timestamp}_COST"
    output_dir = OUTPUT_DIR / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "cost_estimate.md"

    # Pre-compute summary stats
    min_cost_per_video = min((c['cost_per_video'] for c in cost_data), default=0)
    max_cost_per_video = max((c['cost_per_video'] for c in cost_data), default=0)
    avg_cost_per_video = (
        sum(c['cost_per_video'] for c in cost_data) / len(cost_data) if cost_data else 0
    )
    total_profiles = len(cost_data)
    
    with open(report_path, 'w') as f:
        # Title
        f.write("# Cost Estimation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Put all summary information at the top
        f.write("## Summary\n\n")
        f.write(f"- **Total Videos:** {num_triplets}\n")
        f.write(f"- **Profiles Evaluated:** {total_profiles}\n")
        f.write(f"- **Avg Cost/Video (across profiles):** ${avg_cost_per_video:.4f}\n")
        f.write(f"- **Cost/Video Range:** ${min_cost_per_video:.4f} – ${max_cost_per_video:.4f}\n\n")
        
        # Cost table near top as part of summary
        f.write("## Cost by Profile\n\n")
        f.write("| Profile | Model | Cost/Second | Total Duration | Total Cost | Avg Cost/Video |\n")
        f.write("|---------|-------|-------------|----------------|------------|----------------|\n")
        for cost in cost_data:
            f.write(f"| {cost['profile']} | {cost['model']} | ${cost['cost_per_second']:.4f} | ")
            f.write(f"{cost['total_seconds']}s | **${cost['total_cost']:.4f}** | ")
            f.write(f"${cost['cost_per_video']:.4f} |\n")
        
        # Detailed section follows after the summaries
        f.write("\n## Video Duration Distribution (First Profile)\n\n")
        f.write("| Video | Input Frames | Video Duration |\n")
        f.write("|-------|--------------|----------------|\n")
        for item in duration_list:
            adjusted_marker = " ⚠️" if item.get('adjusted') else ""
            f.write(f"| {item['prompt']} | {item['frames']} | {item['duration']}s{adjusted_marker} |\n")
        
        # Calculate total for first profile
        total_first = sum(item['duration'] for item in duration_list)
        f.write(f"| **TOTAL** | - | **{total_first}s** |\n\n")
        f.write("*⚠️ = Duration adjusted to meet model min/max constraints*\n\n")
        
        f.write("## Notes\n\n")
        f.write("- All pricing is time-based (cost per second of video output)\n")
        f.write("- This is an estimate based on configured profiles\n")
        f.write("- Actual costs may vary if generation fails or retries are needed\n")
    
    return report_path


def estimate_costs() -> None:
    """Calculate and report cost estimates without generating videos."""
    logger.info("Starting cost estimation...")
    
    try:
        # Load data
        profiles, triplets = load_estimation_data()
        
        # Calculate costs
        cost_data, duration_list, profile_totals = calculate_all_costs(profiles, triplets)
        
        # Generate report
        report_path = generate_cost_report(cost_data, duration_list, profile_totals, len(triplets))
        
        logger.info(f"Cost estimation report saved to: {report_path}")
        logger.success(f"✅ Cost estimation complete! Report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise


if __name__ == "__main__":
    estimate_costs()