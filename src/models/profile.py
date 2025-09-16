"""Video profile model."""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VideoProfile:
    """Video generation profile configuration."""
    name: str
    model_id: str
    nickname: str
    pricing: Dict[str, float]
    parameters: Dict[str, Any]
    
