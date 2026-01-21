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
    Validate that profiles exist. Markdown file validation is deferred until
    after profiles are loaded, since profiles may specify custom input paths.

    Args:
        input_dir: Default directory for markdown job files (may be overridden by profiles)
        profiles_dir: Directory containing profile YAML files

    Raises:
        InputValidationError: If required directories don't exist or no profiles found
    """
    # Check default input directory exists (profiles may override this)
    if not input_dir.exists():
        error_msg = f"Default input directory does not exist: {input_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    # Check for profiles - this is required before we can check for markdown files
    # since profiles may specify custom input paths
    if not list(profiles_dir.glob("*.yaml")) and not list(profiles_dir.glob("*.yml")):
        error_msg = f"No profiles found in {profiles_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    logger.info("Profiles directory validated successfully")
