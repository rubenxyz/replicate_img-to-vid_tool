"""Verbose terminal output configuration for real-time visibility."""
import sys
import time
from typing import Optional, Any
from loguru import logger
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, 
    TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
)
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live


# Create console for output to stderr (won't interfere with stdout)
console = Console(stderr=True, force_terminal=True)


def setup_verbose_output() -> None:
    """Configure console output for verbose mode with minimal colors."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with INFO level and minimal colors
    logger.add(
        sys.stderr,
        level="INFO",
        format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Thread-safe for background polling
    )
    
    # Configure color scheme - only ERROR and SUCCESS
    logger.level("ERROR", color="<red><bold>")
    logger.level("SUCCESS", color="<green><bold>")
    logger.level("INFO", color="<white>")
    logger.level("WARNING", color="<yellow>")
    logger.level("DEBUG", color="<dim>")


def create_progress_display() -> Progress:
    """Create enhanced progress bar with additional columns."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn("[dim]{task.fields[status]}"),
        console=console,
        refresh_per_second=2,
    )


def create_layout_display(progress: Progress) -> Layout:
    """Create Rich layout with progress bar and log area."""
    layout = Layout()
    
    # Simple two-panel layout
    layout.split_column(
        Layout(Panel(progress, title="Progress", border_style="blue"), size=5),
        Layout(name="logs", ratio=1)
    )
    
    return layout


def log_stage_emoji(stage: str, message: str) -> None:
    """Log with emoji stage indicators."""
    emojis = {
        "starting": "🚀",
        "preparing": "📋",
        "api_call": "📡",
        "queued": "⏳",
        "processing": "⚙️",
        "downloading": "📥",
        "saving": "💾",
        "complete": "✅",
        "failed": "❌",
        "retry": "🔄"
    }
    
    emoji = emojis.get(stage.lower(), "▶️")
    logger.info(f"{emoji} {message}")


def show_error_with_retry(error: Exception, attempt: int, max_attempts: int, wait_time: int) -> None:
    """Display full error traceback with retry countdown."""
    logger.error(f"Attempt {attempt}/{max_attempts} failed:")
    logger.exception(error)
    
    if attempt < max_attempts:
        logger.warning(f"🔄 Retrying in {wait_time} seconds...")
        # Countdown display
        for remaining in range(wait_time, 0, -1):
            console.print(f"  [{remaining}s]", end="\r")
            time.sleep(1)
        console.print("         ", end="\r")  # Clear countdown


class VerboseContext:
    """Context manager for verbose output mode."""
    
    def __init__(self) -> None:
        self.progress: Optional[Progress] = None
        self.layout: Optional[Layout] = None
        self.live: Optional[Live] = None
        
    def __enter__(self) -> 'VerboseContext':
        setup_verbose_output()
        self.progress = create_progress_display()
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self.live:
            self.live.stop()
        return False
        
    def start_live_display(self) -> None:
        """Start live display with layout."""
        if not self.live:
            self.layout = create_layout_display(self.progress)
            self.live = Live(self.layout, console=console, refresh_per_second=2)
            self.live.start()
            
    def update_logs(self, content: str) -> None:
        """Update the logs panel."""
        if self.layout:
            self.layout["logs"].update(Panel(content, title="Logs", border_style="dim"))