"""Hybrid progress implementation using BOTH Rich and alive-progress for maximum impact."""
from typing import Optional, Callable, Dict, Any
from contextlib import contextmanager
from alive_progress import alive_bar, config_handler
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


# Configure alive-progress global defaults
config_handler.set_global(
    length=60,
    spinner='dots_waves',
    bar='smooth',
    theme='smooth',
    force_tty=True,
    dual_line=True,  # Enable dual-line for longer messages
    enrich_print=True,
    calibrate=1000000,
)


class HybridVideoProgress:
    """
    Hybrid progress using alive-progress for main task + Rich for detailed logging.
    
    Strategy (per manifesto):
    - alive-progress: Main video generation progress (maximum visual flair)
    - Rich: Detailed sub-operation logging (console output, panels, formatting)
    
    This gives us:
    - Beautiful animated main progress with dual-line status
    - Detailed Rich-formatted console output for each operation
    - Best of both worlds: visual appeal + professional logging
    """
    
    def __init__(self):
        """Initialize hybrid progress system."""
        self.console = Console(stderr=True, force_terminal=True)
        self.bar = None
        self.current_video = None
        self.total_cost = 0.0
        
    @contextmanager
    def track_generation(self, total_videos: int, title: str = "Video Generation"):
        """
        Track video generation with alive-progress bar + Rich logging.
        
        Args:
            total_videos: Total number of videos to generate
            title: Progress bar title
            
        Yields:
            Tuple of (bar, console) for updates
        """
        # Print Rich header
        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]🎬 {title}[/bold cyan]\n"
            f"[dim]Total videos: {total_videos}[/dim]",
            border_style="cyan",
            padding=(1, 2)
        ))
        self.console.print()
        
        # Main progress with alive-progress (maximum visual flair!)
        with alive_bar(
            total_videos,
            title=f'🎬 {title}',
            bar='smooth',
            spinner='dots_waves',
            dual_line=True,  # Put lengthy text below the bar
            unit='videos',
            unit_scale=False,
        ) as bar:
            self.bar = bar
            try:
                yield bar, self.console
            finally:
                self.bar = None
                self.current_video = None
    
    def update_video_status(
        self,
        video_name: str,
        phase: str,
        details: Optional[str] = None
    ) -> None:
        """
        Update current video status with dual-line display.
        
        Args:
            video_name: Current video name
            phase: Processing phase
            details: Optional additional details
        """
        self.current_video = video_name
        
        # Build dual-line status (appears BELOW the progress bar)
        status_line1 = f"→ [cyan]{video_name}[/cyan]"
        status_line2 = f"   Phase: [yellow]{phase}[/yellow]"
        
        if details:
            status_line2 += f" | {details}"
        
        if self.total_cost > 0:
            status_line2 += f" | [green]Cost: ${self.total_cost:.2f}[/green]"
        
        # Update alive-progress dual-line text
        if self.bar:
            self.bar.text = f"{status_line1}\n{status_line2}"
    
    def log_phase_start(self, phase: str, details: str) -> None:
        """
        Log phase start with Rich formatting.
        
        Args:
            phase: Phase name
            details: Phase details
        """
        emoji_map = {
            'Initializing': '🚀',
            'Preparing': '📋',
            'API Call': '📡',
            'Generating': '⚙️',
            'Downloading': '📥',
            'Finalizing': '💾'
        }
        
        emoji = emoji_map.get(phase, '▶️')
        self.console.print(f"{emoji} [bold]{phase}:[/bold] [dim]{details}[/dim]")
    
    def log_api_status(self, status: str, percentage: Optional[float] = None) -> None:
        """
        Log API status updates.
        
        Args:
            status: API status
            percentage: Optional percentage complete
        """
        status_emoji = {
            'starting': '🚀',
            'queued': '⏳',
            'processing': '⚙️',
            'succeeded': '✅',
            'failed': '❌'
        }
        
        emoji = status_emoji.get(status.lower(), '▶️')
        
        if percentage is not None:
            msg = f"{emoji} API: [cyan]{status.title()}[/cyan] ([bold]{percentage:.0f}%[/bold])"
        else:
            msg = f"{emoji} API: [cyan]{status.title()}[/cyan]"
        
        self.console.print(f"  {msg}")
    
    def mark_success(self, video_name: str, cost: float) -> None:
        """
        Mark video as successfully completed.
        
        Args:
            video_name: Video name
            cost: Video generation cost
        """
        self.total_cost += cost
        
        # Rich console output
        self.console.print(f"[green]✓[/green] [bold]{video_name}[/bold] - [green]${cost:.2f}[/green]")
        
        # Advance alive-progress bar
        if self.bar:
            self.bar()
    
    def mark_error(self, video_name: str, error_msg: str) -> None:
        """
        Mark video as failed.
        
        Args:
            video_name: Video name
            error_msg: Error message
        """
        # Rich console output with detailed error
        self.console.print(
            f"[red]✗[/red] [bold]{video_name}[/bold]",
            style="red"
        )
        self.console.print(
            Panel(
                f"[red]{error_msg}[/red]",
                title="[red]Error",
                border_style="red",
                padding=(0, 2)
            )
        )
        
        # Still advance the bar (fail-fast mode)
        if self.bar:
            self.bar()
    
    def print_summary(self, total: int, success: int, total_cost: float) -> None:
        """
        Print final summary with Rich formatting.
        
        Args:
            total: Total videos
            success: Successful videos
            total_cost: Total cost
        """
        self.console.print()
        
        failed = total - success
        status_color = "green" if failed == 0 else "yellow" if success > 0 else "red"
        
        summary_text = Text()
        summary_text.append("📊 Generation Summary\n\n", style="bold cyan")
        summary_text.append(f"Total Videos: ", style="bold")
        summary_text.append(f"{total}\n")
        summary_text.append(f"Successful: ", style="bold")
        summary_text.append(f"{success}\n", style="green")
        
        if failed > 0:
            summary_text.append(f"Failed: ", style="bold")
            summary_text.append(f"{failed}\n", style="red")
        
        summary_text.append(f"\nTotal Cost: ", style="bold")
        summary_text.append(f"${total_cost:.2f}", style="green bold")
        
        if success > 0:
            avg_cost = total_cost / success
            summary_text.append(f"\nAvg Cost/Video: ", style="bold")
            summary_text.append(f"${avg_cost:.2f}", style="green")
        
        self.console.print(Panel(
            summary_text,
            border_style=status_color,
            padding=(1, 2)
        ))


def create_hybrid_api_callback(
    hybrid: HybridVideoProgress
) -> Callable[[str, Optional[float]], None]:
    """
    Create API callback for hybrid progress.
    
    Args:
        hybrid: HybridVideoProgress instance
        
    Returns:
        Callback function
    """
    def callback(status: str, percentage: Optional[float]):
        """Update progress based on API status."""
        hybrid.log_api_status(status, percentage)
        
        # Update dual-line status
        if hybrid.current_video:
            details = f"API: {status.title()}"
            if percentage is not None:
                details += f" ({percentage:.0f}%)"
            
            hybrid.update_video_status(
                hybrid.current_video,
                "Generating",
                details
            )
    
    return callback


# Example usage template
def example_hybrid_usage():
    """
    Example showing how to use hybrid progress.
    
    This demonstrates the manifesto's recommended approach:
    - alive-progress for main task (beautiful animations, dual-line status)
    - Rich for detailed sub-operation logging (formatted output, panels)
    """
    from time import sleep
    
    videos = [
        {'name': 'video01', 'cost': 0.15},
        {'name': 'video02', 'cost': 0.12},
        {'name': 'video03', 'cost': 0.18},
    ]
    
    hybrid = HybridVideoProgress()
    
    with hybrid.track_generation(len(videos), "Example Generation") as (bar, console):
        for video in videos:
            # Update main status
            hybrid.update_video_status(
                video['name'],
                "Initializing",
                "Setting up context"
            )
            sleep(0.5)
            
            # Log phase with Rich
            hybrid.log_phase_start("Preparing", "Building API parameters")
            sleep(0.5)
            
            # Update to generating phase
            hybrid.update_video_status(
                video['name'],
                "Generating",
                "Sending API request"
            )
            
            # Simulate API updates
            hybrid.log_api_status("starting")
            sleep(0.5)
            hybrid.log_api_status("processing", 50)
            sleep(0.5)
            hybrid.log_api_status("processing", 85)
            sleep(0.5)
            hybrid.log_api_status("succeeded", 100)
            
            # Log download
            hybrid.log_phase_start("Downloading", "Fetching generated video")
            sleep(0.5)
            
            # Mark success (advances bar automatically)
            hybrid.mark_success(video['name'], video['cost'])
        
        # Print summary
        hybrid.print_summary(len(videos), len(videos), sum(v['cost'] for v in videos))


if __name__ == "__main__":
    # Run example
    example_hybrid_usage()
