"""Epic progress bar implementation following the manifesto standards."""
from typing import Optional, Any, Callable, TYPE_CHECKING
from contextlib import contextmanager
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    TaskID,
)
from rich.console import Console
from rich.panel import Panel
from rich.console import Group
from rich.live import Live


class EpicProgress:
    """
    Epic progress bar implementation with all manifesto requirements.
    
    Features:
    - Visual bar with color-coded completion state
    - Animated spinner for active tasks
    - Current item/operation display
    - Numeric progress (X of Y)
    - Time elapsed
    - Time remaining/ETA
    - Processing rate
    - Proper error handling
    - Color coding for status
    - Custom fields support
    """
    
    def __init__(self, console: Optional[Console] = None, transient: bool = False):
        """
        Initialize epic progress bar.
        
        Args:
            console: Optional Rich console instance
            transient: If True, progress bar disappears on completion
        """
        self.console = console or Console(stderr=True, force_terminal=True)
        self.transient = transient
        self.progress: Optional[Progress] = None
        self.live: Optional[Live] = None
        
    def create_progress(self) -> Progress:
        """
        Create progress bar with all epic columns.
        
        Returns:
            Configured Progress instance
        """
        return Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(show_speed=False),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(elapsed_when_finished=True, compact=False),
            TextColumn("[dim]{task.fields[status]}"),
            console=self.console,
            transient=self.transient,
            expand=False,
            refresh_per_second=10,
        )
    
    @contextmanager
    def create_with_panel(self, title: str = "Video Generation Progress"):
        """
        Create progress with panel wrapper for enhanced visibility.
        
        Args:
            title: Panel title
            
        Yields:
            Progress instance
        """
        self.progress = self.create_progress()
        
        # Wrap progress in a panel for better visual separation
        progress_panel = Panel(
            self.progress,
            title=f"[bold cyan]{title}",
            border_style="cyan",
            padding=(0, 1)
        )
        
        self.live = Live(progress_panel, console=self.console, refresh_per_second=4)
        
        try:
            self.live.start()
            yield self.progress
        finally:
            self.live.stop()
            self.progress = None
            self.live = None
    
    @contextmanager
    def create_simple(self):
        """
        Create simple progress without panel.
        
        Yields:
            Progress instance
        """
        self.progress = self.create_progress()
        
        try:
            self.progress.start()
            yield self.progress
        finally:
            self.progress.stop()
            self.progress = None


class VideoGenerationProgress:
    """
    Specialized progress bar for video generation with domain-specific features.
    
    Features:
    - Main task tracking (overall progress)
    - Individual video tracking
    - Status field for current operation
    - Cost tracking
    - Model/profile information
    - Error state indication
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize video generation progress.
        
        Args:
            console: Optional Rich console instance
        """
        self.console = console or Console(stderr=True, force_terminal=True)
        self.progress: Optional[Progress] = None
        self.main_task_id: Optional[TaskID] = None
        
    def create_progress(self) -> Progress:
        """
        Create progress optimized for video generation.
        
        Returns:
            Configured Progress instance
        """
        return Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]{task.description}", justify="left"),
            BarColumn(
                complete_style="green",
                finished_style="bold green",
                bar_width=40
            ),
            TaskProgressColumn(show_speed=False),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(elapsed_when_finished=True, compact=False),
            TextColumn("[dim]{task.fields[status]}", justify="right"),
            console=self.console,
            transient=False,
            expand=False,
            refresh_per_second=10,
        )
    
    @contextmanager
    def track_generation(self, total_videos: int, title: str = "Video Generation"):
        """
        Context manager for tracking video generation progress.
        
        Args:
            total_videos: Total number of videos to generate
            title: Progress bar title
            
        Yields:
            Tuple of (progress, main_task_id)
        """
        self.progress = self.create_progress()
        
        # Wrap in panel for visual separation
        progress_panel = Panel(
            self.progress,
            title=f"[bold cyan]🎬 {title}",
            border_style="cyan",
            padding=(0, 1)
        )
        
        with Live(progress_panel, console=self.console, refresh_per_second=4):
            # Add main task
            self.main_task_id = self.progress.add_task(
                f"[cyan]Processing {total_videos} videos",
                total=total_videos,
                status="Starting..."
            )
            
            try:
                yield self.progress, self.main_task_id
            finally:
                self.progress = None
                self.main_task_id = None
    
    def update_status(
        self,
        progress: Progress,
        task_id: TaskID,
        status: str,
        video_name: Optional[str] = None,
        phase: Optional[str] = None
    ) -> None:
        """
        Update progress status with rich information.
        
        Args:
            progress: Progress instance
            task_id: Task ID to update
            status: Status message
            video_name: Optional current video name
            phase: Optional processing phase
        """
        # Build description
        if video_name:
            description = f"[cyan]{video_name}"
        else:
            task = progress._tasks[task_id]  # type: ignore
            description = task.description
        
        # Build status field
        status_parts = []
        if phase:
            status_parts.append(f"[yellow]{phase}")
        status_parts.append(status)
        status_text = " | ".join(status_parts)
        
        progress.update(
            task_id,
            description=description,
            status=status_text
        )
    
    def update_with_cost(
        self,
        progress: Progress,
        task_id: TaskID,
        status: str,
        total_cost: float,
        video_name: Optional[str] = None
    ) -> None:
        """
        Update progress with cost information.
        
        Args:
            progress: Progress instance
            task_id: Task ID to update
            status: Status message
            total_cost: Total cost so far
            video_name: Optional current video name
        """
        # Build status with cost
        status_text = f"{status} | [green]${total_cost:.2f}"
        
        if video_name:
            description = f"[cyan]{video_name}"
        else:
            task = progress._tasks[task_id]  # type: ignore
            description = task.description
        
        progress.update(
            task_id,
            description=description,
            status=status_text
        )
    
    def mark_error(
        self,
        progress: Progress,
        task_id: TaskID,
        video_name: str,
        error_msg: str
    ) -> None:
        """
        Mark video as failed with error indication.
        
        Args:
            progress: Progress instance
            task_id: Task ID to update
            video_name: Video name
            error_msg: Error message
        """
        progress.update(
            task_id,
            description=f"[red]{video_name}",
            status=f"[red]❌ Failed: {error_msg[:50]}"
        )
        
        # Log to console
        self.console.print(f"[red]✗ {video_name}: {error_msg}")
    
    def mark_success(
        self,
        progress: Progress,
        task_id: TaskID,
        video_name: str,
        cost: float
    ) -> None:
        """
        Mark video as successfully completed.
        
        Args:
            progress: Progress instance
            task_id: Task ID to update
            video_name: Video name
            cost: Video generation cost
        """
        progress.update(
            task_id,
            description=f"[green]{video_name}",
            status=f"[green]✅ Complete (${cost:.2f})"
        )
        
        # Log to console
        self.console.print(f"[green]✓ {video_name} - ${cost:.2f}")


def create_api_callback(
    progress: Progress,
    task_id: TaskID,
    console: Console
) -> Callable[[str, Optional[float]], None]:
    """
    Create callback for API polling progress updates.
    
    Args:
        progress: Progress instance
        task_id: Task ID to update
        console: Console for logging
        
    Returns:
        Callback function for progress updates
    """
    def callback(status: str, percentage: Optional[float]):
        """Update progress based on API status."""
        # Map status to emojis
        status_emoji = {
            'starting': '🚀',
            'processing': '⚙️',
            'succeeded': '✅',
            'failed': '❌',
            'queued': '⏳'
        }
        
        emoji = status_emoji.get(status.lower(), '▶️')
        
        if percentage is not None:
            status_text = f"{emoji} {status.title()} ({percentage:.0f}%)"
        else:
            status_text = f"{emoji} {status.title()}"
        
        progress.update(task_id, status=status_text)
    
    return callback


# Convenience function for simple use cases
def create_epic_progress(
    title: str = "Processing",
    transient: bool = False,
    with_panel: bool = True
) -> EpicProgress:
    """
    Create an epic progress bar with sensible defaults.
    
    Args:
        title: Progress bar title
        transient: If True, disappears on completion
        with_panel: If True, wraps in a panel
        
    Returns:
        EpicProgress instance
    """
    return EpicProgress(transient=transient)
