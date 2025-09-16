"""Environment variable authentication fallback."""
import os
from pathlib import Path
from typing import Optional
from loguru import logger
from dotenv import load_dotenv


def get_replicate_api_token_from_env() -> Optional[str]:
    """
    Retrieve Replicate API token from environment or .env file.
    
    Returns:
        API token string if successful, None if not found
    """
    # Try loading from .env file in project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded environment from {env_path}")
    
    # Get from environment
    api_token = os.getenv("REPLICATE_API_TOKEN")
    
    if api_token:
        logger.info("Successfully retrieved Replicate API token from environment")
        return api_token
    else:
        logger.warning("REPLICATE_API_TOKEN not found in environment")
        return None