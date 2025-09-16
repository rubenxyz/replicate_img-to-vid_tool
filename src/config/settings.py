"""Video generation settings and paths."""
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
USER_FILES_DIR = PROJECT_ROOT / "USER-FILES"

# Input directories for triplet matching
PROMPT_DIR = USER_FILES_DIR / "04.INPUT" / "04.1.PROMPT"
IMAGE_URL_DIR = USER_FILES_DIR / "04.INPUT" / "04.2.IMAGE_URL"
NUM_FRAMES_DIR = USER_FILES_DIR / "04.INPUT" / "04.3.NUM_FRAMES"

# Output directory
OUTPUT_DIR = USER_FILES_DIR / "05.OUTPUT"

# Profile directory
PROFILES_DIR = USER_FILES_DIR / "03.PROFILES"

# Download settings
DOWNLOAD_CHUNK_SIZE = 8192
DOWNLOAD_TIMEOUT = 300  # 5 minutes for video downloads