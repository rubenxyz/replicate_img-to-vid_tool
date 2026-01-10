"""File management utilities for output generation."""
import shutil
from pathlib import Path
from loguru import logger


class FileManager:
    """Manager for output file operations."""

    @staticmethod
    def copy_source_file(source_file: Path, output_dir: Path,
                        video_filename_stem: str) -> None:
        """
        Copy source markdown file for reference with video filename prefix.

        Args:
            source_file: Path to source markdown file
            output_dir: Destination directory
            video_filename_stem: Video filename stem to use as prefix
        """
        try:
            dest_filename = f"{video_filename_stem}_source.md"
            shutil.copy2(source_file, output_dir / dest_filename)
            logger.debug(f"Copied source file to {output_dir / dest_filename}")
        except Exception as e:
            logger.warning(f"Failed to copy source file: {e}")