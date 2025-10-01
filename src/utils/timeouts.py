"""Timeout configuration utilities for API clients."""
import httpx
from ..config.constants import TIMEOUT_CONNECT, TIMEOUT_READ, TIMEOUT_WRITE, TIMEOUT_POOL


def create_video_timeout() -> httpx.Timeout:
    """
    Create timeout configuration optimized for video generation.
    
    Video generation can take several minutes, so we need longer timeouts
    than typical API requests.
    
    Returns:
        httpx.Timeout configured for video generation
    """
    return httpx.Timeout(
        connect=TIMEOUT_CONNECT,
        read=TIMEOUT_READ,
        write=TIMEOUT_WRITE,
        pool=TIMEOUT_POOL
    )