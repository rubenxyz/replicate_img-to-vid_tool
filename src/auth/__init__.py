"""Authentication module for Replicate API."""
from typing import Optional
from .env import get_replicate_api_token_from_env
from .op_auth import get_replicate_api_token_from_op, AuthError


def authenticate(use_1password: bool = True, config_name: Optional[str] = None) -> str:
    """
    Authenticate with Replicate API.

    Default behavior (use_1password=True):
    - Discover USER-FILES/01.CONFIG/auth*.yml/.yaml and read Replicate OP item/field from them.
    - Use 1Password CLI to fetch the token based on those fields.
    - If no valid auth YAML is found or OP lookup fails, raise a clear error (no implicit env fallback).

    If use_1password=False, fall back to REPLICATE_API_TOKEN from environment/.env.

    Args:
        use_1password: Prefer 1Password via auth*.yml/.yaml (default True)
        config_name: Optional specific auth config filename (e.g., 'auth_bites.yaml')

    Returns:
        API token string

    Raises:
        ValueError: If no API token can be found
        AuthError: If 1Password authentication fails
    """
    if use_1password:
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

    # Explicit env fallback path
    api_token = get_replicate_api_token_from_env()
    if not api_token:
        raise ValueError(
            "REPLICATE_API_TOKEN not found in environment. Either provide auth*.yaml for 1Password auth "
            "or set REPLICATE_API_TOKEN."
        )
    return api_token
