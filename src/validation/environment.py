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
        logger.error("No API key found")
        raise AuthenticationError("No API key found. Please set REPLICATE_API_TOKEN environment variable.")
    
    return api_key


def validate_input_directories(prompt_dir: Path, image_url_dir: Path, 
                              num_frames_dir: Path, profiles_dir: Path) -> None:
    """
    Validate that all required input directories contain files.
    
    Args:
        prompt_dir: Directory containing prompt files
        image_url_dir: Directory containing image URL files
        num_frames_dir: Directory containing num frames files
        profiles_dir: Directory containing profile YAML files
        
    Raises:
        InputValidationError: If any required directory is empty
    """
    # Check for prompt files
    if not list(prompt_dir.glob("*.txt")):
        error_msg = f"No prompt files found in {prompt_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)
    
    # Check for image URL files
    if not list(image_url_dir.glob("*.txt")):
        error_msg = f"No image URL files found in {image_url_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)
    
    # Check for num frames files
    if not list(num_frames_dir.glob("*.txt")):
        error_msg = f"No num frames files found in {num_frames_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)
    
    # Check for profiles
    if not list(profiles_dir.glob("*.yaml")) and not list(profiles_dir.glob("*.yml")):
        error_msg = f"No profiles found in {profiles_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)
    
    logger.info("All input directories validated successfully")