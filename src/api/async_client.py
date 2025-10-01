"""Async Replicate client with polling for verbose output."""
import os
import time
from typing import Dict, Any, Optional, Callable
from ..models.video_processing import VideoRequest
from loguru import logger
from replicate.prediction import Prediction
from replicate.client import Client

from ..utils.verbose_output import log_stage_emoji, show_error_with_retry
from ..utils.timeouts import create_video_timeout


class AsyncReplicateClient:
    """Replicate client with async prediction polling for progress visibility."""
    
    def __init__(
        self,
        api_token: str,
        poll_interval: int = 3,
        max_wait_time: int = 1200,
        max_retries: int = 3,
        rate_limit_retry_delay: int = 60
    ):
        """
        Initialize async Replicate client.
        
        Args:
            api_token: Replicate API token
            poll_interval: Seconds between status checks
            max_wait_time: Max time to wait for completion
            max_retries: Number of retry attempts
            rate_limit_retry_delay: Delay when rate limited
        """
        self.api_token = api_token
        self.poll_interval = poll_interval
        self.max_wait_time = max_wait_time
        self.max_retries = max_retries
        self.rate_limit_retry_delay = rate_limit_retry_delay
        
        # Set API token for replicate module
        os.environ['REPLICATE_API_TOKEN'] = api_token
        
        # Initialize client with custom timeout for video generation
        self.client = Client(
            api_token=api_token,
            timeout=create_video_timeout()
        )
        
    def generate_video_with_polling(
        self,
        model_name: str,
        image_url: str,
        prompt: str,
        params: Dict[str, Any],
        progress_callback: Optional[Callable[[str, Optional[float]], None]] = None
    ) -> Optional[str]:
        """Generate video with polling - convenience wrapper."""
        request = VideoRequest(
            model_name=model_name,
            image_url=image_url,
            prompt=prompt,
            params=params,
            progress_callback=progress_callback
        )
        return self.generate_video_from_request(request)
    
    def generate_video_from_request(
        self,
        request: VideoRequest
    ) -> Optional[str]:
        """
        Generate video with status polling for visibility.
        
        Args:
            request: VideoRequest with all generation parameters
            
        Returns:
            Video URL if successful, None otherwise
        """
        # Build payload
        payload = {
            "image": request.image_url,
            "prompt": request.prompt,
            **request.params
        }
        
        log_stage_emoji("api_call", f"Sending request to {request.model_name}")
        
        # Create prediction with retry logic
        prediction = self._create_prediction_with_retry(request.model_name, payload)
        if not prediction:
            return None
            
        # Poll for completion
        return self._poll_prediction(prediction, request.progress_callback)
        
    def _create_prediction_with_retry(
        self,
        model: str,
        payload: Dict[str, Any]
    ) -> Optional[Prediction]:
        """Create prediction with retry logic."""
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Creating prediction (attempt {attempt}/{self.max_retries})")
                
                # Create prediction (non-blocking)
                prediction = self.client.predictions.create(
                    model=model,
                    input=payload
                )
                
                log_stage_emoji("queued", f"Prediction created: {prediction.id}")
                return prediction
                
            except Exception as e:
                last_error = e
                
                # Handle rate limiting
                if "429" in str(e) or "rate" in str(e).lower():
                    wait_time = self.rate_limit_retry_delay
                else:
                    wait_time = 2 ** attempt  # Exponential backoff
                    
                show_error_with_retry(e, attempt, self.max_retries, wait_time)
                
                if attempt < self.max_retries:
                    time.sleep(wait_time)
                    
        logger.error(f"Failed to create prediction after {self.max_retries} attempts")
        return None
        
    def _poll_prediction(
        self,
        prediction: Prediction,
        progress_callback: Optional[Callable[[str, Optional[float]], None]] = None
    ) -> Optional[str]:
        """
        Poll prediction status until completion.
        
        Args:
            prediction: The prediction to poll
            progress_callback: Optional callback for progress updates
            
        Returns:
            Output URL if successful
        """
        start_time = time.time()
        last_status = None
        last_progress = None
        
        while True:
            # Check timeout
            if time.time() - start_time > self.max_wait_time:
                logger.error(f"Timeout: Prediction {prediction.id} took too long")
                return None
                
            # Reload prediction status
            try:
                prediction.reload()
            except Exception as e:
                logger.error(f"Failed to reload prediction: {e}")
                return None
                
            # Log status changes
            if prediction.status != last_status:
                self._log_status_change(prediction.status, last_status)
                last_status = prediction.status
                
            # Extract and log progress if available
            progress_pct = self._extract_progress(prediction)
            if progress_pct != last_progress:
                if progress_pct is not None:
                    logger.info(f"Processing: {progress_pct:.0f}% complete")
                last_progress = progress_pct
                
            # Callback for external progress tracking
            if progress_callback:
                progress_callback(prediction.status, progress_pct)
                
            # Check completion states
            if prediction.status == "succeeded":
                return self._extract_output_url(prediction)
            elif prediction.status == "failed":
                logger.error(f"Prediction failed: {prediction.error}")
                return None
            elif prediction.status == "canceled":
                logger.warning("Prediction was canceled")
                return None
                
            # Wait before next poll
            time.sleep(self.poll_interval)
            
    def _log_status_change(self, new_status: str, old_status: Optional[str]) -> None:
        """Log status changes with appropriate emojis."""
        if new_status == "starting":
            log_stage_emoji("starting", "Prediction starting...")
        elif new_status == "processing":
            if old_status == "starting":
                log_stage_emoji("processing", "Now processing video generation")
        elif new_status == "succeeded":
            log_stage_emoji("complete", "Video generation completed!")
            
    def _extract_progress(self, prediction: Prediction) -> Optional[float]:
        """Extract progress percentage from prediction if available."""
        # Check for progress in logs
        if prediction.logs:
            # Look for percentage patterns in logs
            import re
            match = re.search(r'(\d+(?:\.\d+)?)\s*%', prediction.logs)
            if match:
                return float(match.group(1))
                
        # Check for progress field (some models provide this)
        if hasattr(prediction, 'progress') and prediction.progress:
            if hasattr(prediction.progress, 'percentage'):
                return prediction.progress.percentage * 100
                
        return None
        
    def _extract_output_url(self, prediction: Prediction) -> Optional[str]:
        """Extract video URL from prediction output."""
        output = prediction.output
        
        if not output:
            logger.error("No output from prediction")
            return None
            
        logger.debug(f"Output type: {type(output)}, value: {output}")
        
        # Handle different output formats
        if isinstance(output, str):
            return output
        elif hasattr(output, 'url'):
            return output.url
        elif isinstance(output, list) and len(output) > 0:
            first_item = output[0]
            if hasattr(first_item, 'url'):
                return first_item.url
            elif isinstance(first_item, str):
                return first_item
        else:
            # Try converting to string
            result_str = str(output)
            if result_str.startswith('http'):
                return result_str
                
        logger.error(f"Could not extract URL from output: {output}")
        return None


# PollingThread moved to polling_handler.py