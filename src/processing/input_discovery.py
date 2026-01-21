"""Input discovery for markdown job files."""

import re
from pathlib import Path
from typing import List, Optional
from loguru import logger
from natsort import natsorted

from ..models.triplet import MarkdownJob


def discover_markdown_jobs(
    input_dir: Path, custom_input_path: Optional[str] = None
) -> List[Path]:
    """
    Discover markdown job files in input directory.

    Args:
        input_dir: Default input directory (USER-FILES/04.INPUT)
        custom_input_path: Optional custom input path from profile

    Returns:
        List of markdown file paths, naturally sorted

    Raises:
        FileNotFoundError: If directory doesn't exist or no markdown files found
    """
    # Use custom path if provided, otherwise use default input directory
    if custom_input_path:
        effective_input_dir = Path(custom_input_path)
        logger.info(f"Using custom input directory: {effective_input_dir}")
    else:
        effective_input_dir = input_dir

    if not effective_input_dir.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {effective_input_dir}"
        )

    # Get all markdown files
    markdown_files = list(effective_input_dir.glob("*.md"))

    if not markdown_files:
        raise FileNotFoundError(
            f"No markdown (.md) files found in {effective_input_dir}"
        )

    # Natural sort for consistent ordering
    markdown_files = natsorted(markdown_files)

    logger.info(f"Found {len(markdown_files)} markdown job files")
    for i, md_file in enumerate(markdown_files, 1):
        logger.debug(f"Job {i}: {md_file.name}")

    return markdown_files


def parse_markdown_job(markdown_file: Path) -> MarkdownJob:
    """
    Parse markdown job file with 3-line format:
    Line 1: Video prompt text
    Line 2: num_frames integer
    Line 3: Embedded image with URL ![...](URL)

    Args:
        markdown_file: Path to markdown job file

    Returns:
        MarkdownJob object with parsed data

    Raises:
        ValueError: If file format is invalid or data cannot be parsed
    """
    try:
        content = markdown_file.read_text()
        lines = content.split("\n")

        # Ensure we have at least 3 lines
        if len(lines) < 3:
            raise ValueError(
                f"Markdown file must have at least 3 lines, found {len(lines)} lines"
            )

        # Line 1: Prompt text
        prompt = lines[0].strip()
        if not prompt:
            raise ValueError("Line 1 (prompt) is empty")

        # Line 2: num_frames integer
        num_frames_str = lines[1].strip()
        if not num_frames_str:
            raise ValueError("Line 2 (num_frames) is empty")

        try:
            num_frames = int(num_frames_str)
            if num_frames < 1:
                raise ValueError(f"num_frames must be at least 1, got {num_frames}")
        except ValueError as e:
            raise ValueError(f"Line 2 must be a valid integer (num_frames): {e}")

        # Line 3: Extract URL from markdown image syntax
        image_line = lines[2].strip()
        if not image_line:
            raise ValueError("Line 3 (image URL) is empty")

        # Match markdown image format: ![alt](URL) or ![](URL)
        image_pattern = r"!\[.*?\]\((https?://[^\s)]+)\)"
        match = re.search(image_pattern, image_line)

        if not match:
            raise ValueError(
                f"Line 3 must contain markdown image format: ![alt](URL)\n"
                f"Found: {image_line}"
            )

        image_url = match.group(1)

        logger.debug(
            f"Parsed {markdown_file.name}: prompt='{prompt[:30]}...', "
            f"frames={num_frames}, url='{image_url[:50]}...'"
        )

        return MarkdownJob(
            markdown_file=markdown_file,
            prompt=prompt,
            num_frames=num_frames,
            image_url=image_url,
        )

    except Exception as e:
        logger.error(f"Failed to parse {markdown_file.name}: {e}")
        raise ValueError(f"Invalid markdown job file {markdown_file.name}: {e}")
