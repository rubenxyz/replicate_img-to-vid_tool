"""Processing context models."""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from rich.progress import Progress

from ..api.client import ReplicateClient


@dataclass
class ProcessingContext:
    """Context for matrix processing operations."""
    client: ReplicateClient
    prompt_dir: Path
    image_url_dir: Path
    num_frames_dir: Path
    profiles_dir: Path
    output_dir: Path
    progress: Optional[Progress] = None