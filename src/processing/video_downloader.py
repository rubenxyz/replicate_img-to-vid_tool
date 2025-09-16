"""Video download functionality."""
from pathlib import Path
from loguru import logger
import requests

from ..config.settings import DOWNLOAD_CHUNK_SIZE, DOWNLOAD_TIMEOUT


def download_video(url: str, output_path: Path) -> None:
    """
    Download video from URL.
    
    Args:
        url: Video URL from Replicate API
        output_path: Local path to save video
        
    Raises:
        Exception: On download failure
    """
    try:
        logger.debug(f"Downloading video from: {url[:100]}...")
        
        response = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {percent:.1f}%")
        
        logger.info(f"Saved video: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to download video: {e}")
        raise