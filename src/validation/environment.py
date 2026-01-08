"""Environment and directory validation utilities."""

from pathlib import Path
from loguru import logger

from ..auth import authenticate
from ..exceptions import AuthenticationError, InputValidationError


def validate_environment() -> str:
    """
    Validate environment and authentication.

    Returns:
        API key if authentication successful

    Raises:
        AuthenticationError: If authentication fails
    """
    logger.info("Starting image-to-video generation")

    api_key = authenticate()
    if not api_key:
        logger.error("No API key found via 1Password")
        raise AuthenticationError(
            "No API key found. Please ensure USER-FILES/01.CONFIG/auth*.yaml exists "
            "with valid 1Password credentials."
        )

    return api_key


def validate_input_directories(input_dir: Path, profiles_dir: Path) -> None:
    """
    Validate that input directory contains markdown job files and profiles exist.

    Args:
        input_dir: Directory containing markdown job files
        profiles_dir: Directory containing profile YAML files

    Raises:
        InputValidationError: If required directories are empty or don't exist
    """
    # Check input directory exists
    if not input_dir.exists():
        error_msg = f"Input directory does not exist: {input_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    # Check for markdown job files
    if not list(input_dir.glob("*.md")):
        error_msg = f"No markdown (.md) job files found in {input_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    # Check for profiles
    if not list(profiles_dir.glob("*.yaml")) and not list(profiles_dir.glob("*.yml")):
        error_msg = f"No profiles found in {profiles_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    logger.info("Input directory and profiles validated successfully")
