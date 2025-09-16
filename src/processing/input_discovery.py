"""Input discovery for prompt-link-duration triplets."""
from pathlib import Path
from typing import List, Tuple
from loguru import logger
from natsort import natsorted


def discover_input_triplets(prompt_dir: Path, image_url_dir: Path, 
                           num_frames_dir: Path) -> List[Tuple[Path, Path, Path]]:
    """
    Discover matching prompt, image URL, and num frame file triplets by chronological order.
    
    Files are matched by their sort order, not by filename.
    First file in prompt matches first file in image_url and first file in num_frames.
    
    Args:
        prompt_dir: Directory containing prompt text files
        image_url_dir: Directory containing image URL text files  
        num_frames_dir: Directory containing num frames text files
        
    Returns:
        List of (prompt_file, image_url_file, num_frames_file) tuples
        
    Raises:
        FileNotFoundError: If directories don't exist
        ValueError: If number of files don't match across directories
    """
    # Get all text files from each directory
    prompt_files = list(prompt_dir.glob("*.txt"))
    image_url_files = list(image_url_dir.glob("*.txt"))
    num_frames_files = list(num_frames_dir.glob("*.txt"))
    
    # Check if we have files
    if not prompt_files:
        raise FileNotFoundError(f"No prompt files found in {prompt_dir}")
    if not image_url_files:
        raise FileNotFoundError(f"No image URL files found in {image_url_dir}")
    if not num_frames_files:
        raise FileNotFoundError(f"No num frames files found in {num_frames_dir}")
    
    # Check if counts match
    if len(prompt_files) != len(image_url_files) or len(prompt_files) != len(num_frames_files):
        raise ValueError(
            f"File count mismatch: {len(prompt_files)} prompts, "
            f"{len(image_url_files)} image URLs, {len(num_frames_files)} num frames"
        )
    
    # Natural sort all file lists for consistent ordering
    prompt_files = natsorted(prompt_files)
    image_url_files = natsorted(image_url_files)
    num_frames_files = natsorted(num_frames_files)
    
    # Create triplets by matching indices
    triplets = []
    for i, (prompt_file, image_url_file, num_frames_file) in enumerate(
        zip(prompt_files, image_url_files, num_frames_files)
    ):
        triplets.append((prompt_file, image_url_file, num_frames_file))
        logger.debug(
            f"Triplet {i+1}: {prompt_file.name} + {image_url_file.name} + {num_frames_file.name}"
        )
    
    logger.info(f"Found {len(triplets)} input triplets (matched by order)")
    return triplets


def load_input_data(prompt_file: Path, image_url_file: Path, 
                   num_frames_file: Path) -> Tuple[str, str, int]:
    """
    Load prompt text, image URL, and num_frames from files.
    
    Args:
        prompt_file: Path to prompt text file
        image_url_file: Path to image URL file
        num_frames_file: Path to num frames file
        
    Returns:
        Tuple of (prompt, image_url, num_frames)
        
    Raises:
        ValueError: If files are empty or contain invalid data
    """
    try:
        prompt = prompt_file.read_text().strip()
        image_url = image_url_file.read_text().strip()
        num_frames_str = num_frames_file.read_text().strip()
        
        if not prompt:
            raise ValueError(f"Empty prompt file: {prompt_file}")
        if not image_url:
            raise ValueError(f"Empty image URL file: {image_url_file}")
        if not num_frames_str:
            raise ValueError(f"Empty num frames file: {num_frames_file}")
        
        # Validate URL format
        if not (image_url.startswith("http://") or image_url.startswith("https://")):
            raise ValueError(f"Invalid URL in {image_url_file}: {image_url}")
        
        # Parse num_frames as integer
        try:
            num_frames = int(num_frames_str)
            if num_frames < 1:
                raise ValueError(f"num_frames must be at least 1, got {num_frames}")
        except ValueError as e:
            raise ValueError(f"Invalid num_frames in {num_frames_file}: {e}")
        
        logger.debug(f"Loaded: prompt='{prompt[:30]}...', url='{image_url[:50]}...', frames={num_frames}")
        return prompt, image_url, num_frames
        
    except Exception as e:
        logger.error(f"Failed to load files: {e}")
        raise