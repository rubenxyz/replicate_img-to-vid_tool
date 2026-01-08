"""Markdown job model."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MarkdownJob:
    """Markdown job file containing prompt, num_frames, and image URL."""

    markdown_file: Path
    prompt: str
    num_frames: int
    image_url: str
