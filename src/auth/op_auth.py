"""1Password CLI authentication module."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
import yaml
from loguru import logger


OP_CLI = shutil.which("op")


class AuthError(Exception):
    """Custom exception for authentication errors."""
    pass


def ensure_op_auth() -> None:
    """
    Ensures 1Password CLI is authenticated, handling the interactive sign-in
    process by capturing the session token from stdout.

    Raises:
        FileNotFoundError: If 1Password CLI is not installed
        AuthError: If authentication fails
    """
    if not OP_CLI:
        raise FileNotFoundError("1Password CLI not found. Please install it.")

    try:
        # First, a lightweight check to see if we're already signed in.
        subprocess.run(
            [OP_CLI, "account", "get"], check=True, capture_output=True, timeout=10
        )
        logger.debug("1Password session is active.")
        return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.info("🔐 1Password session expired or not found. Signing in...")
        try:
            # The 'op signin' command prompts on stderr and prints the session
            # key to stdout. We need to let the user see the prompt and type
            # their password.
            signin_process = subprocess.Popen(
                [OP_CLI, "signin"],
                stdout=subprocess.PIPE,
                stderr=sys.stderr,  # Pass through to the user's terminal
                stdin=sys.stdin,  # Allow the user to type their password
                text=True,
            )
            stdout, _ = signin_process.communicate(timeout=60)

            if signin_process.returncode != 0:
                raise AuthError("Failed to authenticate with 1Password during sign-in.")

            # The output of `op signin` is a shell command like:
            # export OP_SESSION_my_account="..."
            # We parse it and set the environment variable in our own process.
            if stdout:
                for line in stdout.strip().split("\n"):
                    if line.startswith("export "):
                        line = line.replace("export ", "")
                        key, value = line.split("=", 1)
                        value = value.strip('"')  # Remove quotes
                        os.environ[key] = value
                        logger.debug(f"Set 1Password session variable: {key}")
            logger.info("✅ 1Password sign-in successful.")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error("❌ Failed to authenticate with 1Password.")
            if isinstance(e, subprocess.CalledProcessError) and e.stderr:
                logger.error(f"1Password CLI error:\n{e.stderr}")
            raise AuthError("Failed to authenticate with 1Password") from e


def get_secret(item_name: str, field_name: str) -> str:
    """
    Retrieve a secret from 1Password after ensuring authentication.

    Args:
        item_name: Name of the 1Password item
        field_name: Name of the field within the item

    Returns:
        The secret value as a string

    Raises:
        AuthError: If authentication fails
        subprocess.CalledProcessError: If the secret cannot be retrieved
    """
    ensure_op_auth()

    try:
        secret = subprocess.check_output(
            [OP_CLI, "item", "get", item_name, "--field", field_name],
            text=True,
            timeout=10
        ).strip()
        logger.debug(f"Successfully retrieved secret from 1Password item '{item_name}'")
        return secret
    except subprocess.CalledProcessError as e:
        logger.error(f"Could not retrieve secret from 1Password: {e}")
        raise


def load_auth_config(config_name: str = "auth_ruben.yaml") -> dict:
    """
    Load authentication configuration from YAML file.

    Args:
        config_name: Name of the auth config file (default: auth_ruben.yaml)

    Returns:
        Dictionary containing authentication configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_path = Path(__file__).parent.parent.parent / "USER-FILES" / "01.CONFIG" / config_name

    if not config_path.exists():
        raise FileNotFoundError(f"Auth config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    logger.debug(f"Loaded auth config from {config_path}")
    return config


def get_replicate_api_token_from_op(config_name: str = "auth_ruben.yaml") -> Optional[str]:
    """
    Retrieve Replicate API token from 1Password using configuration file.

    Args:
        config_name: Name of the auth config file (default: auth_ruben.yaml)

    Returns:
        API token string if successful, None if not found

    Raises:
        AuthError: If authentication fails
        FileNotFoundError: If config file doesn't exist
    """
    try:
        config = load_auth_config(config_name)

        if "replicate" not in config:
            logger.error("No 'replicate' section found in auth config")
            return None

        item_name = config["replicate"]["item_name"]
        field_name = config["replicate"]["field_name"]

        logger.info(f"Retrieving Replicate API token from 1Password item '{item_name}'")
        api_token = get_secret(item_name, field_name)

        if api_token:
            logger.info("✅ Successfully retrieved Replicate API token from 1Password")
            return api_token
        else:
            logger.warning("Retrieved empty API token from 1Password")
            return None

    except (FileNotFoundError, KeyError, AuthError) as e:
        logger.error(f"Failed to retrieve API token from 1Password: {e}")
        raise
