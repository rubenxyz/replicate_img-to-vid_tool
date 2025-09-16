#!/usr/bin/env python
"""Standalone cost estimation script - calculates costs without generating videos."""
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from src.processing.input_discovery import discover_input_triplets
from src.processing.profile_loader import load_active_profiles
from src.processing.cost_calculator import calculate_video_cost
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


def calculate_all_costs(profiles: List[Dict[str, Any]], triplets: List[Tuple[Path, Path, Path]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Calculate costs for all profiles and frame counts.
    
    Args:
        profiles: List of profile dictionaries
        triplets: List of input file triplets
        
    Returns:
        Tuple of (cost_data, frame_counts, total_frames)
    """
    # Read frame counts
    total_frames = 0
    frame_counts = []
    
    for prompt_file, _, num_frames_file in triplets:
        try:
            num_frames_str = num_frames_file.read_text().strip()
            num_frames = int(num_frames_str)
            total_frames += num_frames
            frame_counts.append({
                'prompt': prompt_file.stem,
                'frames': num_frames
            })
            logger.info(f"{prompt_file.stem}: {num_frames} frames")
        except Exception as e:
            logger.error(f"Failed to read frame count from {num_frames_file}: {e}")
            continue
    
    # Calculate costs for each profile
    cost_data = []
    for profile in profiles:
        try:
            total_cost = calculate_video_cost(profile, total_frames)
            cost_per_video = total_cost / len(triplets) if triplets else 0
            
            # Get pricing info safely
            pricing = profile.get('pricing', {})
            cost_per_frame = pricing.get('cost_per_frame', 0)
            
            cost_data.append({
                'profile': profile['name'],
                'model': profile['model_id'],
                'cost_per_frame': cost_per_frame,
                'total_frames': total_frames,
                'total_cost': total_cost,
                'cost_per_video': cost_per_video,
                'num_videos': len(triplets)
            })
            
            logger.info(f"Profile '{profile['name']}': ${total_cost:.4f} for {total_frames} frames")
        except Exception as e:
            logger.error(f"Failed to calculate cost for profile {profile['name']}: {e}")
    
    return cost_data, frame_counts, total_frames


def generate_cost_report(cost_data: List[Dict[str, Any]], frame_counts: List[Dict[str, Any]], 
                         total_frames: int, num_triplets: int) -> Path:
    """
    Generate markdown cost estimation report.
    
    Args:
        cost_data: List of cost calculations per profile
        frame_counts: List of frame counts per video
        total_frames: Total frame count
        num_triplets: Number of input triplets
        
    Returns:
        Path to generated report
    """
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    output_dir = OUTPUT_DIR / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "cost_estimate.md"
    
    with open(report_path, 'w') as f:
        f.write("# Cost Estimation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Input Summary\n\n")
        f.write(f"- **Total Videos:** {num_triplets}\n")
        f.write(f"- **Total Frames:** {total_frames}\n")
        f.write(f"- **Average Frames per Video:** {total_frames / num_triplets:.0f}\n\n")
        
        f.write("## Frame Distribution\n\n")
        f.write("| Video | Frames |\n")
        f.write("|-------|--------|\n")
        for item in frame_counts:
            f.write(f"| {item['prompt']} | {item['frames']} |\n")
        f.write(f"| **TOTAL** | **{total_frames}** |\n\n")
        
        f.write("## Cost by Profile\n\n")
        f.write("| Profile | Model | Cost/Frame | Total Frames | Total Cost | Avg Cost/Video |\n")
        f.write("|---------|-------|------------|--------------|------------|----------------|\n")
        
        for cost in cost_data:
            f.write(f"| {cost['profile']} | {cost['model']} | ${cost['cost_per_frame']:.4f} | ")
            f.write(f"{cost['total_frames']} | **${cost['total_cost']:.4f}** | ")
            f.write(f"${cost['cost_per_video']:.4f} |\n")
        
        f.write("\n## Notes\n\n")
        f.write("- All pricing is frame-based (cost per frame in USD)\n")
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
        cost_data, frame_counts, total_frames = calculate_all_costs(profiles, triplets)
        
        # Generate report
        report_path = generate_cost_report(cost_data, frame_counts, total_frames, len(triplets))
        
        logger.info(f"Cost estimation report saved to: {report_path}")
        logger.success(f"✅ Cost estimation complete! Report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise


if __name__ == "__main__":
    estimate_costs()