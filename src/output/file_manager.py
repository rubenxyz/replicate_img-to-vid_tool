"""File management utilities for output generation."""
import shutil
from pathlib import Path
from loguru import logger


class FileManager:
    """Manager for output file operations."""
    
    @staticmethod
    def copy_source_files(prompt_file: Path, image_url_file: Path, 
                         num_frames_file: Path, output_dir: Path) -> None:
        """
        Copy source files for reference.
        
        Args:
            prompt_file: Path to prompt file
            image_url_file: Path to image URL file
            num_frames_file: Path to num frames file
            output_dir: Destination directory
        """
        try:
            shutil.copy2(prompt_file, output_dir / f"source_{prompt_file.name}")
            shutil.copy2(image_url_file, output_dir / f"source_{image_url_file.name}")
            shutil.copy2(num_frames_file, output_dir / f"source_{num_frames_file.name}")
            logger.debug(f"Copied source files to {output_dir}")
        except Exception as e:
            logger.warning(f"Failed to copy some source files: {e}")