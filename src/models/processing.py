"""Processing context models."""

from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

from ..api.client import ReplicateClient


@dataclass
class ProcessingContext:
    """Context for matrix processing operations."""

    client: ReplicateClient
    input_dir: Path
    profiles_dir: Path
    output_dir: Path
    progress: Optional[Any] = None
