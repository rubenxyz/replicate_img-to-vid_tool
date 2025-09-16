"""Generation context model."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class GenerationContext:
    """Context for video generation with all required data."""
    prompt_file: Path
    image_url_file: Path
    num_frames_file: Path
    output_dir: Path
    prompt: str
    image_url: str
    num_frames: int
    profile: Dict[str, Any]
    params: Dict[str, Any]
    video_url: str
    video_path: Path
    cost: float
    adjustment_info: Optional[Dict[str, Any]] = None