"""Input triplet model."""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Tuple


@dataclass
class InputTriplet:
    """Input file triplet for video generation."""
    prompt_file: Path
    image_url_file: Path
    num_frames_file: Path
    
    def __iter__(self) -> Iterator[Path]:
        """Allow unpacking of triplet."""
        return iter((self.prompt_file, self.image_url_file, self.num_frames_file))