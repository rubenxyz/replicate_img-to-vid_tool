"""Verbose terminal output configuration for real-time visibility."""

import sys
import time
from typing import TYPE_CHECKING, Optional, Any, Union, List, Dict
from loguru import logger

if TYPE_CHECKING:
    from alive_progress import alive_bar

    ALIVE_PROGRESS_AVAILABLE = True
else:
    try:
        from alive_progress import alive_bar

        ALIVE_PROGRESS_AVAILABLE = True
    except ImportError:
        ALIVE_PROGRESS_AVAILABLE = False
        alive_bar = None


console_stderr = sys.stderr


def setup_verbose_output() -> None:
    """Configure console output for verbose mode with minimal colors."""
    try:
        from .enhanced_logging import CONSOLE_HANDLER_ID

        if CONSOLE_HANDLER_ID is not None:
            logger.remove(CONSOLE_HANDLER_ID)
    except (ImportError, ValueError):
        pass

    logger.add(
        sys.stderr,
        level="INFO",
        format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    logger.level("ERROR", color="<red><bold>")
    logger.level("SUCCESS", color="<green><bold>")
    logger.level("INFO", color="<white>")
    logger.level("WARNING", color="<yellow>")
    logger.level("DEBUG", color="<dim>")


class VerboseProgress:
    """Progress bar for verbose mode using alive-progress."""

    def __init__(self, **kwargs: Any) -> None:
        self._bar: Any = None
        self._kwargs = kwargs

    def __enter__(self) -> "VerboseProgress":
        if ALIVE_PROGRESS_AVAILABLE and alive_bar:
            self._bar = alive_bar(**self._kwargs)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self._bar is not None:
            try:
                self._bar.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass
        return False

    def __call__(self, advance: Union[int, float] = 1) -> None:
        if self._bar is not None:
            try:
                self._bar(advance)
            except Exception:
                pass

    @property
    def text(self) -> str:
        if self._bar is not None and hasattr(self._bar, "text"):
            return str(self._bar.text)
        return ""

    @text.setter
    def text(self, value: str) -> None:
        if self._bar is not None and hasattr(self._bar, "text"):
            self._bar.text = value


def create_progress_display() -> VerboseProgress:
    """Create enhanced progress bar."""
    return VerboseProgress(
        title="Progress",
        bar="smooth",
        spinner="dots_waves",
        dual_line=True,
        stats=True,
        monitor=True,
        elapsed=True,
    )


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
        "retry": "🔄",
    }

    emoji = emojis.get(stage.lower(), "▶️")
    logger.info(f"{emoji} {message}")


def show_error_with_retry(
    error: Exception, attempt: int, max_attempts: int, wait_time: int
) -> None:
    """Display full error traceback with retry countdown."""
    logger.error(f"Attempt {attempt}/{max_attempts} failed:")
    logger.exception(error)

    if attempt < max_attempts:
        logger.warning(f"🔄 Retrying in {wait_time} seconds...")
        for remaining in range(wait_time, 0, -1):
            console_stderr.write(f"  [{remaining}s]\r")
            console_stderr.flush()
            time.sleep(1)
        console_stderr.write("         \r")


def show_project_header(profiles: List[Dict[str, Any]]) -> None:
    """
    Display project name header in console output.

    Args:
        profiles: List of profile configurations with optional project_name
    """
    # Collect unique project names
    project_names = set()
    for profile in profiles:
        project_name = profile.get("project_name")
        if project_name:
            project_names.add(project_name)

    if project_names:
        # Display in a banner format
        for name in sorted(project_names):
            logger.info(f"[bold cyan]━━━━━━━ {name} ━━━━━━━[/]")


class VerboseContext:
    """Context manager for verbose output mode."""

    def __init__(self) -> None:
        self.progress: Optional[VerboseProgress] = None

    def __enter__(self) -> "VerboseContext":
        setup_verbose_output()
        self.progress = create_progress_display()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
        return False
