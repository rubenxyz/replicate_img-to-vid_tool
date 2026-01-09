"""Video processing context models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class VideoProcessingContext:
    """Context for processing a single video."""

    client: Any  # Supports AsyncReplicateClient, AsyncReplicateClientEnhanced, etc.
    prompt_file: Path
    image_url_file: Path
    num_frames_file: Path
    profile: Dict[str, Any]
    run_dir: Path
    progress: Any  # Rich Progress object
    task_id: int


@dataclass
class APIClientConfig:
    """Configuration for API clients."""

    api_token: str
    poll_interval: int = 3
    max_wait_time: int = 1200
    max_retries: int = 3
    rate_limit_retry_delay: int = 60


@dataclass
class VideoGenerationRequest:
    """Request for generating and downloading a video."""

    client: Any  # ReplicateClient or async variants
    profile: Dict[str, Any]
    image_url: str
    prompt: str
    params: Dict[str, Any]
    output_dir: Path
    markdown_file: Path


@dataclass
class VideoRequest:
    """Request data for video generation."""

    model_name: str
    image_url: str
    prompt: str
    params: Dict[str, Any]
    progress_callback: Optional[Any] = None
    image_url_param: str = "image"
