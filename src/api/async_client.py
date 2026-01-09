"""Async Replicate client with polling for verbose output."""

import time
from typing import Optional, Callable
from loguru import logger
from replicate.prediction import Prediction

from .base_async_client import BaseAsyncReplicateClient
from ..models.video_processing import APIClientConfig


class AsyncReplicateClient(BaseAsyncReplicateClient):
    """Replicate client with async prediction polling for progress visibility."""

    def _poll_prediction(
        self,
        prediction: Prediction,
        progress_callback: Optional[Callable[[str, Optional[float]], None]] = None,
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
