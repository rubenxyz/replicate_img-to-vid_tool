"""Authentication module for Replicate API."""
from loguru import logger
from .env import get_replicate_api_token_from_env


def authenticate() -> str:
    """
    Authenticate with Replicate API using environment variables.
    
    Returns:
        API token string
        
    Raises:
        ValueError: If no API token can be found
    """
    # Get from environment
    api_token = get_replicate_api_token_from_env()
    
    if not api_token:
        raise ValueError(
            "Failed to authenticate. No Replicate API token found.\n"
            "Please set REPLICATE_API_TOKEN in .env file or environment"
        )
    
    return api_token