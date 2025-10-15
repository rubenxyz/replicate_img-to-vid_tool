"""1Password CLI authentication module."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Iterator
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


# --- Auth config discovery helpers ---
CONFIG_DIR = Path(__file__).parent.parent.parent / "USER-FILES" / "01.CONFIG"


def find_auth_config_paths() -> List[Path]:
    """Return all USER-FILES/01.CONFIG files named 'auth*.yml' or 'auth*.yaml'."""
    patterns = ["auth*.yaml", "auth*.yml"]
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(sorted(CONFIG_DIR.glob(pattern)))
    return paths


def load_auth_config_from_path(path: Path) -> dict:
    """Load a single auth config YAML file by exact path."""
    if not path.exists():
        raise FileNotFoundError(f"Auth config file not found: {path}")
    with open(path, "r") as f:
        cfg = yaml.safe_load(f) or {}
    logger.debug(f"Loaded auth config from {path}")
    return cfg


def iter_auth_configs() -> Iterator[Tuple[dict, Path]]:
    """Iterate over all discovered auth configs, yielding (config, path)."""
    for path in find_auth_config_paths():
        try:
            yield load_auth_config_from_path(path), path
        except Exception as e:
            logger.warning(f"Skipping invalid auth config {path}: {e}")
            continue


def load_auth_config(config_name: str = "auth_ruben.yaml") -> dict:
    """
    Load authentication configuration from YAML file by name (legacy helper).
    """
    config_path = CONFIG_DIR / config_name
    return load_auth_config_from_path(config_path)


def get_replicate_api_token_from_op(config_name: Optional[str] = None) -> Optional[str]:
    """
    Retrieve Replicate API token from 1Password using configuration file(s).

    Args:
        config_name: Optional specific auth config file name. If None, try all auth*.yml/.yaml files.

    Returns:
        API token string if successful, None if not found

    Raises:
        AuthError: If authentication fails
    """
    try:
        # If a specific config is provided, use it first
        if config_name:
            config = load_auth_config(config_name)
            configs: List[Tuple[dict, Path]] = [(config, CONFIG_DIR / config_name)]
        else:
            configs = list(iter_auth_configs())
            if not configs:
                logger.warning(f"No auth*.yml/.yaml files found in {CONFIG_DIR}")
                return None

        for cfg, path in configs:
            rep = cfg.get("replicate") or {}
            item_name = rep.get("item_name")
            field_name = rep.get("field_name")
            if not item_name or not field_name:
                logger.warning(f"Missing replicate.item_name/field_name in {path.name}; skipping")
                continue

            logger.info(f"Retrieving Replicate API token from 1Password (config: {path.name})")
            try:
                api_token = get_secret(item_name, field_name)
            except Exception as e:
                logger.warning(f"Failed with config {path.name}: {e}; trying next if available")
                continue

            if api_token:
                logger.info("✅ Successfully retrieved Replicate API token from 1Password")
                return api_token
            else:
                logger.warning(f"Empty API token returned using {path.name}; trying next if available")
                continue

        logger.error("No valid Replicate API token found in any auth*.yaml/.yml config")
        return None

    except AuthError as e:
        logger.error(f"Failed to retrieve API token from 1Password: {e}")
        raise
