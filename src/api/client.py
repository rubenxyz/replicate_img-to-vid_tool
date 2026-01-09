"""Replicate API client wrapper for video generation."""

import os
import time
from typing import Dict, Any, Optional
from loguru import logger
from replicate.client import Client
from ..utils.timeouts import create_video_timeout
from ..models.video_processing import APIClientConfig


class ReplicateClient:
    """Wrapper for Replicate with sequential video processing."""

    def __init__(self, config: APIClientConfig, timeout: int = 300):
        """
        Initialize Replicate client for video generation.

        Args:
            config: APIClientConfig with API token and behavior settings
            timeout: Request timeout in seconds (longer for video)
        """
        self.api_token = config.api_token
        self.timeout = timeout
        self.max_retries = config.max_retries
        self.max_wait_time = config.max_wait_time
        self.rate_limit_retry_delay = config.rate_limit_retry_delay

        # Set API token in environment for replicate module
        os.environ["REPLICATE_API_TOKEN"] = config.api_token

        # Create client with custom timeout for video generation
        self.client = Client(api_token=config.api_token, timeout=create_video_timeout())

    def generate_video(
        self,
        model_name: str,
        image_url: str,
        prompt: str,
        params: Dict[str, Any],
        image_url_param: str = "image",
    ) -> Optional[str]:
        """
        Generate video from image URL using Replicate API.

        Args:
            model_name: Replicate model name (e.g., 'owner/model:version')
            image_url: Direct URL to source image
            prompt: Motion description text
            params: Video-specific parameters
            image_url_param: Parameter name for image URL (from profile)

        Returns:
            Video URL if successful, None otherwise

        Raises:
            Exception: On API failure after retries
        """
        # Build video-specific payload for Replicate
        payload = {
            image_url_param: image_url,  # Use parameter name from profile
            "prompt": prompt,  # Motion description from prompt file
            **params,  # Video-specific parameters
        }

        logger.info(f"Generating video with prompt: {prompt[:50]}...")

        # Sequential processing
        result = self._call_with_retry(model_name, payload)

        # Parse response to extract video URL
        return self._parse_video_response(result)

    def _parse_video_response(self, result: Any) -> Optional[str]:
        """
        Parse API response to extract video URL.

        Args:
            result: API response (various types possible)

        Returns:
            Video URL if found, None otherwise
        """
        if not result:
            logger.error("No result from Replicate API")
            return None

        logger.debug(f"Result type: {type(result)}, value: {result}")

        # Response type handlers
        handlers = {str: self._handle_string_response, list: self._handle_list_response}

        # Check for direct type match
        result_type = type(result)
        if result_type in handlers:
            return handlers[result_type](result)

        # Check for FileOutput object
        if hasattr(result, "url"):
            return self._handle_file_output(result)

        # Fallback to string conversion
        return self._handle_fallback(result)

    def _handle_string_response(self, result: str) -> str:
        """Handle string response."""
        logger.info(f"Successfully got video URL: {result}")
        return result

    def _handle_file_output(self, result: Any) -> str:
        """Handle FileOutput response."""
        logger.info(f"Successfully got video URL from FileOutput: {result.url}")
        return result.url

    def _handle_list_response(self, result: list) -> Optional[str]:
        """Handle list response."""
        if not result:
            return None

        first_item = result[0]
        if hasattr(first_item, "url"):
            logger.info(
                f"Successfully got video URL from list FileOutput: {first_item.url}"
            )
            return first_item.url
        else:
            logger.info(f"Successfully got video URL from list: {first_item}")
            return first_item

    def _handle_fallback(self, result: Any) -> Optional[str]:
        """Handle unknown response types."""
        result_str = str(result)
        if result_str.startswith("http"):
            logger.info(f"Successfully converted result to URL: {result_str}")
            return result_str
        else:
            logger.error(
                f"Unexpected response format - type: {type(result)}, value: {result}"
            )
            return None

    def _call_with_retry(self, model: str, payload: Dict[str, Any]) -> Any:
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

                # Use client.run for synchronous execution with custom timeout
                result = self.client.run(model, input=payload)

                logger.debug("API call successful")
                return result

            except Exception as e:
                last_error = e

                # Check if it's a rate limit error
                if "429" in str(e) or "rate" in str(e).lower():
                    logger.warning(
                        f"Rate limited, waiting {self.rate_limit_retry_delay}s..."
                    )
                    time.sleep(self.rate_limit_retry_delay)
                    continue

                # Other errors
                logger.error(f"Error on attempt {attempt}: {e}")

                if attempt < self.max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

        # All retries exhausted
        raise Exception(f"Failed after {self.max_retries} attempts: {last_error}")
