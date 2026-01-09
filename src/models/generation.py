"""Generation context model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .triplet import MarkdownJob


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

    @classmethod
    def from_job(
        cls,
        job: "MarkdownJob",
        video_dir: Path,
        profile: Dict[str, Any],
        prompt: str,
        params: Dict[str, Any],
        video_url: str,
        video_path: Path,
        cost: float,
        adjustment_info: Optional[Dict[str, Any]] = None,
    ) -> "GenerationContext":
        """
        Factory method to create context from job data.

        Simplifies creation by using job.markdown_file for all file fields
        and extracting job data automatically.
        """
        return cls(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,
            num_frames_file=job.markdown_file,
            output_dir=video_dir,
            prompt=prompt,
            image_url=job.image_url,
            num_frames=job.num_frames,
            profile=profile,
            params=params,
            video_url=video_url,
            video_path=video_path,
            cost=cost,
            adjustment_info=adjustment_info,
        )
