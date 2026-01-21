"""Logging setup with loguru."""

from pathlib import Path
from loguru import logger
import sys
import os


def _sanitize_for_filename(name: str) -> str:
    """Sanitize string for use in filename."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip()


def setup_logging(
    verbose: bool = False, debug: bool = False, project_name: str | None = None
) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: Enable verbose console output
        debug: Enable debug level logging
        project_name: Optional project name to include in log filename
    """
    # Remove default handler
    logger.remove()

    # Console handler
    level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # File handler with rotation
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Generate log filename with optional project name
    if project_name:
        sanitized_name = _sanitize_for_filename(project_name)
        log_filename = f"{sanitized_name}_wrapper_{{time}}.log"
    else:
        log_filename = "replicate_wrapper_{time}.log"

    logger.add(
        log_dir / log_filename,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info(f"Logging configured (verbose={verbose}, debug={debug})")
