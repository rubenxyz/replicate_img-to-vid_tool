"""Video profile model."""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class VideoProfile:
    """Video generation profile configuration."""
    name: str
    model_id: str
    nickname: str
    pricing: Dict[str, float]
    parameters: Dict[str, Any]
    prompt_suffix: Optional[str] = None
    
