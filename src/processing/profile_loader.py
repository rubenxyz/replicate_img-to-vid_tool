"""Profile loading utilities."""
import yaml
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
from natsort import natsorted

from .profile_validator import ProfileValidator
from ..exceptions import ProfileValidationError


def find_yaml_files(profiles_dir: Path) -> List[Path]:
    """Find all YAML files in the profiles directory."""
    yaml_files = list(profiles_dir.glob("*.yaml"))
    yaml_files.extend(profiles_dir.glob("*.yml"))
    return yaml_files


def load_single_profile(yaml_file: Path) -> Dict[str, Any]:
    """Load and validate a single profile from YAML file."""
    with open(yaml_file, 'r') as f:
        profile_data = yaml.safe_load(f) or {}
    
    profile_name = yaml_file.stem
    validator = ProfileValidator()
    
    # Validate all sections
    model_section = validator.validate_model_section(profile_data, yaml_file)
    pricing = validator.validate_pricing_section(profile_data, yaml_file)
    duration_config = validator.validate_duration_section(profile_data, yaml_file)
    params = validator.validate_params_section(profile_data, yaml_file)
    
    # Build profile dictionary
    profile = {
        "name": profile_name,
        "model_id": model_section['endpoint'],
        "nickname": model_section.get('code-nickname', profile_name),
        "pricing": pricing,
        "parameters": params,
        "duration_config": duration_config
    }
    
    logger.info(f"Loaded profile: {profile_name} (endpoint: {model_section['endpoint']})")
    return profile


def load_active_profiles(profiles_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all active video profiles from YAML files.
    
    Args:
        profiles_dir: Directory containing profile YAML files
        
    Returns:
        List of profile dictionaries with name, model endpoint, pricing, and parameters
        
    Raises:
        FileNotFoundError: If profiles directory doesn't exist
        ProfileValidationError: If no profiles found or invalid format
    """
    if not profiles_dir.exists():
        raise FileNotFoundError(f"Profiles directory not found: {profiles_dir}")
    
    yaml_files = find_yaml_files(profiles_dir)
    
    if not yaml_files:
        raise ProfileValidationError(f"No profile files found in {profiles_dir}")
    
    active_profiles = []
    
    for yaml_file in natsorted(yaml_files):
        try:
            profile = load_single_profile(yaml_file)
            active_profiles.append(profile)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {yaml_file}: {e}")
            raise
    
    if not active_profiles:
        raise ProfileValidationError("No profiles found. Check your profile files in USER-FILES/03.PROFILES/")
    
    logger.info(f"Loaded {len(active_profiles)} profiles")
    return active_profiles