"""Authentication module for Replicate API using 1Password only."""
from typing import Optional
from .op_auth import get_replicate_api_token_from_op, AuthError

__all__ = ['authenticate', 'AuthError']


def authenticate(config_name: Optional[str] = None) -> str:
    """
    Authenticate with Replicate API using 1Password.

    Discovers USER-FILES/01.CONFIG/auth*.yml/.yaml files and retrieves the
    Replicate API token from 1Password based on the item_name and field_name
    specified in the auth config.

    Args:
        config_name: Optional specific auth config filename (e.g., 'auth_bites.yaml')
                    If None, tries all auth*.yml/.yaml files in order

    Returns:
        API token string

    Raises:
        ValueError: If no API token can be found
        AuthError: If 1Password authentication fails
    """
    try:
        api_token = get_replicate_api_token_from_op(config_name)
        if api_token:
            return api_token
    except (AuthError, FileNotFoundError) as e:
        from loguru import logger
        logger.error(f"1Password authentication error: {e}")
        raise
    
    # No token found in any auth*.yaml
    raise ValueError(
        "No valid Replicate token found via 1Password. Ensure a USER-FILES/01.CONFIG/auth*.yaml "
        "exists with 'replicate.item_name' and 'replicate.field_name'."
    )
