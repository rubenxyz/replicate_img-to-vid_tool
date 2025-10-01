"""Progress display utilities for verbose output."""
from typing import Optional, Any
from loguru import logger
from ..utils.verbose_output import log_stage_emoji


def update_progress_status(progress: Any, task_id: int, status: str, percentage: Optional[float] = None) -> None:
    """
    Update progress bar with status and percentage.
    
    Args:
        progress: Rich Progress object
        task_id: Task ID to update
        status: Status message
        percentage: Optional percentage complete
    """
    if percentage is not None:
        progress.update(
            task_id,
            status=f"⚙️ {status.title()} ({percentage:.0f}%)"
        )
    else:
        progress.update(task_id, status=f"⏳ {status.title()}")


def log_progress_change(status: str, percentage: Optional[float] = None) -> None:
    """
    Log progress changes with appropriate formatting.
    
    Args:
        status: Current status
        percentage: Optional percentage complete
    """
    if percentage is not None:
        logger.info(f"Processing: {percentage:.0f}% complete")
    else:
        log_stage_emoji(status.lower(), f"Status: {status}")


def create_progress_callback(progress: Any, task_id: int):
    """
    Create a progress callback function for API calls.
    
    Args:
        progress: Rich Progress object
        task_id: Task ID to update
        
    Returns:
        Callback function for progress updates
    """
    def callback(status: str, percentage: Optional[float]):
        update_progress_status(progress, task_id, status, percentage)
    
    return callback