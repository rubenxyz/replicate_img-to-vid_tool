"""Duration adjustments reporter."""
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger


def create_adjustments_report(adjustments: List[Dict[str, Any]], output_dir: Path, 
                             total_processed: int) -> None:
    """
    Create ADJUSTMENTS.md report for duration changes.
    
    Args:
        adjustments: List of adjustment records
        output_dir: Directory to write report to
        total_processed: Total number of videos processed
    """
    if not adjustments:
        logger.info("No duration adjustments were made")
        return
    
    report_path = output_dir / "ADJUSTMENTS.md"
    
    # Count statistics
    files_adjusted = len(adjustments)
    files_as_is = total_processed - files_adjusted
    
    # Group adjustments by type
    frame_adjustments = [a for a in adjustments if a.get('type') == 'frames']
    second_adjustments = [a for a in adjustments if a.get('type') == 'seconds']
    
    # Build report content
    content = ["# Duration Adjustments Report", ""]
    content.append("## Summary")
    content.append(f"- Total files processed: {total_processed}")
    content.append(f"- Files with adjustments: {files_adjusted}")
    content.append(f"- Files processed as-is: {files_as_is}")
    content.append("")
    
    if frame_adjustments or second_adjustments:
        content.append("## Adjustments Detail")
        content.append("")
        
        # Frame-based adjustments
        if frame_adjustments:
            content.append("### Frame-Based Adjustments")
            for adj in frame_adjustments:
                content.append("")
                content.append(f"#### {adj['prompt_file']}")
                content.append(f"- Profile: {adj['profile']}")
                content.append(f"- Original: {adj['original']} frames")
                content.append(f"- Adjusted: {adj['adjusted']} frames")
                content.append(f"- Reason: {adj['reason']}")
        
        # Second-based adjustments
        if second_adjustments:
            content.append("")
            content.append("### Second-Based Adjustments")
            for adj in second_adjustments:
                content.append("")
                content.append(f"#### {adj['prompt_file']}")
                content.append(f"- Profile: {adj['profile']}")
                content.append(f"- Original: {adj['original_frames']} frames ({adj['original_seconds']}s at {adj['fps']} fps)")
                content.append(f"- Adjusted: {adj['adjusted_seconds']} seconds")
                content.append(f"- Reason: {adj['reason']}")
    
    # Write report
    report_path.write_text("\n".join(content))
    logger.info(f"Duration adjustments report written to: {report_path}")
    logger.info(f"Total adjustments: {files_adjusted}/{total_processed} files modified")