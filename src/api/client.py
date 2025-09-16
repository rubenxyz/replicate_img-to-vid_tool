"""Replicate API client wrapper for video generation."""
import os
import time
from typing import Dict, Any, Optional
from loguru import logger
import replicate


class ReplicateClient:
    """Wrapper for Replicate with sequential video processing."""
    
    def __init__(
        self,
        api_token: str,
        timeout: int = 300,
        max_retries: int = 3,
        max_wait_time: int = 1200,
        rate_limit_retry_delay: int = 60
    ):
        """
        Initialize Replicate client for video generation.
        
        Args:
            api_token: Replicate API token
            timeout: Request timeout in seconds (longer for video)
            max_retries: Number of retry attempts
            max_wait_time: Max time to wait for queued jobs
            rate_limit_retry_delay: Delay when rate limited
        """
        self.api_token = api_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_wait_time = max_wait_time
        self.rate_limit_retry_delay = rate_limit_retry_delay
        
        # Set API token in environment for replicate module
        os.environ['REPLICATE_API_TOKEN'] = api_token
        
    def generate_video(
        self,
        model_name: str,
        image_url: str,
        prompt: str,
        params: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate video from image URL using Replicate API.
        
        Args:
            model_name: Replicate model name (e.g., 'owner/model:version')
            image_url: Direct URL to source image
            prompt: Motion description text
            params: Video-specific parameters
            
        Returns:
            Video URL if successful, None otherwise
            
        Raises:
            Exception: On API failure after retries
        """
        # Build video-specific payload for Replicate
        payload = {
            "image": image_url,  # Replicate uses 'image' not 'image_url'
            "prompt": prompt,  # Motion description from prompt file
            **params  # Video-specific parameters
        }
        
        logger.info(f"Generating video with prompt: {prompt[:50]}...")
        
        # Sequential processing
        result = self._call_with_retry(model_name, payload)
        
        # Extract video URL from result
        if result:
            logger.debug(f"Result type: {type(result)}, value: {result}")
            # Replicate returns the output directly (could be string URL, list, or FileOutput)
            if isinstance(result, str):
                logger.info(f"Successfully got video URL: {result}")
                return result
            elif hasattr(result, 'url'):
                # Handle replicate.helpers.FileOutput objects
                logger.info(f"Successfully got video URL from FileOutput: {result.url}")
                return result.url
            elif isinstance(result, list) and len(result) > 0:
                # Handle lists - check if first item is FileOutput or string
                first_item = result[0]
                if hasattr(first_item, 'url'):
                    logger.info(f"Successfully got video URL from list FileOutput: {first_item.url}")
                    return first_item.url
                else:
                    logger.info(f"Successfully got video URL from list: {first_item}")
                    return first_item
            else:
                # Convert to string as fallback - FileOutput has __str__ method
                result_str = str(result)
                if result_str.startswith('http'):
                    logger.info(f"Successfully converted result to URL: {result_str}")
                    return result_str
                else:
                    logger.error(f"Unexpected response format - type: {type(result)}, value: {result}")
                    return None
        else:
            logger.error("No result from Replicate API")
            return None
    
    def _call_with_retry(
        self,
        model: str,
        payload: Dict[str, Any]
    ) -> Any:
        """
        Call Replicate API with retry logic.
        
        Args:
            model: Model identifier
            payload: Request payload
            
        Returns:
            API response
            
        Raises:
            Exception: After all retries exhausted
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"API call attempt {attempt}/{self.max_retries}")
                
                # Use replicate.run for synchronous execution
                result = replicate.run(
                    model,
                    input=payload
                )
                
                logger.debug("API call successful")
                return result
                
            except Exception as e:
                last_error = e
                
                # Check if it's a rate limit error
                if "429" in str(e) or "rate" in str(e).lower():
                    logger.warning(f"Rate limited, waiting {self.rate_limit_retry_delay}s...")
                    time.sleep(self.rate_limit_retry_delay)
                    continue
                
                # Other errors
                logger.error(f"Error on attempt {attempt}: {e}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        # All retries exhausted
        raise Exception(f"Failed after {self.max_retries} attempts: {last_error}")