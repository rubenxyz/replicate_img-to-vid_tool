"""Enhanced logging that maintains both file and console output."""
from pathlib import Path
from loguru import logger
import sys


# Global variable to track console handler ID
CONSOLE_HANDLER_ID = None


def setup_dual_logging(enable_verbose: bool = True) -> None:
    """
    Configure dual logging - file and console.
    
    Args:
        enable_verbose: Whether to enable verbose console output
    """
    global CONSOLE_HANDLER_ID
    
    # Remove default handler
    logger.remove()
    
    # Always maintain file logging at DEBUG level
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "replicate_wrapper_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True  # Thread-safe
    )
    
    if enable_verbose:
        # Add console handler with INFO level and colors
        CONSOLE_HANDLER_ID = logger.add(
            sys.stderr,
            level="INFO",
            format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}",
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
        
        # Configure minimal colors
        logger.level("ERROR", color="<red><bold>")
        logger.level("SUCCESS", color="<green><bold>")
        logger.level("WARNING", color="<yellow>")
        logger.level("INFO", color="<white>")
        logger.level("DEBUG", color="<dim>")
        
    logger.info(f"Logging configured (verbose={enable_verbose}, file=always)")