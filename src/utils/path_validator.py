"""Path validation utilities for custom input/output directories."""

from pathlib import Path
from loguru import logger


def validate_custom_path(path: Path, path_type: str) -> None:
    """
    Validate that a custom path exists and is accessible.

    Args:
        path: Path to validate
        path_type: Type of path ('input' or 'output') for error messages

    Raises:
        FileNotFoundError: If path doesn't exist
        NotADirectoryError: If path exists but is not a directory
    """
    if not path.exists():
        raise FileNotFoundError(f"Custom {path_type} directory does not exist: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Custom {path_type} path is not a directory: {path}")


def validate_custom_paths(input_path: Path | None, output_path: Path | None) -> None:
    """
    Validate custom input and output paths exist.

    Args:
        input_path: Optional custom input path
        output_path: Optional custom output path

    Raises:
        FileNotFoundError: If any path doesn't exist
        NotADirectoryError: If any path exists but is not a directory
    """
    if input_path:
        logger.debug(f"Validating custom input path: {input_path}")
        validate_custom_path(input_path, "input")

    if output_path:
        logger.debug(f"Validating custom output path: {output_path}")
        validate_custom_path(output_path, "output")
