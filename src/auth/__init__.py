"""Authentication module - prioritizes .env over 1Password."""
from typing import Optional
from .env import get_replicate_api_token_from_env
from .op_auth import get_replicate_api_token_from_op, AuthError

__all__ = ['authenticate', 'AuthError']


def authenticate(config_name: Optional[str] = None) -> str:
    """
    Authenticate with Replicate API - .env priority over 1Password.

    Priority:
    1. REPLICATE_API_TOKEN from .env file or environment
    2. 1Password CLI fallback

    Args:
        config_name: Optional specific auth config filename (e.g., 'auth_bites.yaml')
                    If None, tries all auth*.yml/.yaml files in order

    Returns:
        API token string

    Raises:
        ValueError: If no API token can be found
        AuthError: If 1Password authentication fails
    """
    api_token = get_replicate_api_token_from_env()
    if api_token:
        return api_token
    
    try:
        api_token = get_replicate_api_token_from_op(config_name)
        if api_token:
            return api_token
    except (AuthError, FileNotFoundError) as e:
        from loguru import logger
        logger.error(f"1Password authentication error: {e}")
        raise
    
    raise ValueError(
        "No valid Replicate token found. Ensure a .env file exists with REPLICATE_API_TOKEN "
        "or a USER-FILES/01.CONFIG/auth*.yaml exists with 1Password config."
    )