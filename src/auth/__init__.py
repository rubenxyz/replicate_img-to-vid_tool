"""Authentication module for Replicate API."""
from .env import get_replicate_api_token_from_env
from .op_auth import get_replicate_api_token_from_op, AuthError


def authenticate(use_1password: bool = True, config_name: str = "auth_ruben.yaml") -> str:
    """
    Authenticate with Replicate API using 1Password CLI or environment variables.

    Args:
        use_1password: If True, use 1Password CLI. If False, fall back to .env (default: True)
        config_name: Name of the auth config file for 1Password (default: auth_ruben.yaml)

    Returns:
        API token string

    Raises:
        ValueError: If no API token can be found
        AuthError: If 1Password authentication fails
    """
    if use_1password:
        try:
            # Try 1Password CLI first
            api_token = get_replicate_api_token_from_op(config_name)
            if api_token:
                return api_token
        except (AuthError, FileNotFoundError) as e:
            # Fall back to environment if 1Password fails
            from loguru import logger
            logger.warning(f"1Password authentication failed: {e}. Falling back to .env file...")

    # Fall back to environment variables
    api_token = get_replicate_api_token_from_env()

    if not api_token:
        raise ValueError(
            "Failed to authenticate. No Replicate API token found.\n"
            "Please either:\n"
            "  1. Configure 1Password CLI with auth_ruben.yaml, or\n"
            "  2. Set REPLICATE_API_TOKEN in .env file or environment"
        )

    return api_token