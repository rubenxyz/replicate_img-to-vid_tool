"""Async Replicate client with alive-progress WAVES animation during polling."""

import time
from typing import Optional, Callable
from loguru import logger
from replicate.prediction import Prediction

try:
    from alive_progress import alive_bar

    ALIVE_PROGRESS_AVAILABLE = True
except ImportError:
    ALIVE_PROGRESS_AVAILABLE = False
    logger.warning("alive-progress not installed, falling back to basic polling")

from .base_async_client import BaseAsyncReplicateClient
from ..models.video_processing import APIClientConfig


class AsyncReplicateClientEnhanced(BaseAsyncReplicateClient):
    """Replicate client with WAVES animation during API polling (manifesto feature!)."""

    def _poll_prediction(
        self,
        prediction: Prediction,
        progress_callback: Optional[Callable[[str, Optional[float]], None]] = None,
    ) -> Optional[str]:
        """
        Poll prediction with WAVES animation or basic polling.

        Uses alive-progress WAVES if available, otherwise falls back to basic polling.

        Args:
            prediction: The prediction to poll
            progress_callback: Optional callback for progress updates

        Returns:
            Output URL if successful
        """
        if ALIVE_PROGRESS_AVAILABLE:
            return self._poll_prediction_with_waves(prediction, progress_callback)
        else:
            return self._poll_prediction_basic(prediction, progress_callback)

    def _poll_prediction_with_waves(
        self,
        prediction: Prediction,
        progress_callback: Optional[Callable[[str, Optional[float]], None]] = None,
    ) -> Optional[str]:
        """
        Poll prediction with WAVES animation (manifesto killer feature!).

        This uses alive-progress with the beautiful 'waves' spinner for
        maximum visual appeal while waiting for video generation.
        """
        from alive_progress import alive_bar

        start_time = time.time()
        last_status = None

        # Use alive-progress with smooth animation
        with alive_bar(
            manual=True,
            title="🎬 Generating Video",
            bar="smooth",  # Smooth bar animation
            spinner="dots_waves",  # Animated spinner
            dual_line=True,
            stats=True,
            monitor=True,
            elapsed=True,
        ) as bar:
            while True:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.max_wait_time:
                    logger.error(f"Timeout: Prediction {prediction.id} took too long")
                    return None

                # Reload prediction status
                try:
                    prediction.reload()
                except Exception as e:
                    logger.error(f"Failed to reload prediction: {e}")
                    return None

                # Update status text
                status_text = self._format_status_text(prediction, elapsed)
                bar.text = status_text

                # Log status changes
                if prediction.status != last_status:
                    self._log_status_change(prediction.status, last_status)
                    last_status = prediction.status

                # Extract progress percentage
                progress_pct = self._extract_progress(prediction)

                # Update bar percentage (manual mode)
                if progress_pct is not None:
                    bar(progress_pct / 100.0)  # Convert to 0.0-1.0
                else:
                    # Estimate progress based on status
                    if prediction.status == "starting":
                        bar(0.1)
                    elif prediction.status == "processing":
                        bar(0.5)

                # Callback for external tracking
                if progress_callback:
                    progress_callback(prediction.status, progress_pct)

                # Check completion states
                if prediction.status == "succeeded":
                    bar(1.0)  # 100%
                    bar.text = "✅ Video generation complete!"
                    time.sleep(0.5)  # Show completion briefly
                    return self._extract_output_url(prediction)
                elif prediction.status == "failed":
                    logger.error(f"Prediction failed: {prediction.error}")
                    bar.text = f"❌ Generation failed: {prediction.error}"
                    return None
                elif prediction.status == "canceled":
                    logger.warning("Prediction was canceled")
                    bar.text = "⚠️ Prediction was canceled"
                    return None

                # Wait before next poll
                time.sleep(self.poll_interval)

    def _poll_prediction_basic(
        self,
        prediction: Prediction,
        progress_callback: Optional[Callable[[str, Optional[float]], None]] = None,
    ) -> Optional[str]:
        """Basic polling without waves (fallback when alive-progress not available)."""
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

            # Extract and log progress
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

    def _format_status_text(self, prediction: Prediction, elapsed: float) -> str:
        """Format dual-line status text for waves animation."""
        status_emoji = {
            "starting": "🚀",
            "processing": "⚙️",
            "succeeded": "✅",
            "failed": "❌",
            "queued": "⏳",
        }

        emoji = status_emoji.get(prediction.status, "▶️")

        # Line 1: Status and elapsed time
        elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
        line1 = f"→ {emoji} {prediction.status.upper()} | Elapsed: {elapsed_str}"

        # Line 2: Progress or ID
        progress_pct = self._extract_progress(prediction)
        if progress_pct is not None:
            line2 = f"   Progress: {progress_pct:.0f}% | ID: {prediction.id[:8]}..."
        else:
            line2 = f"   Prediction ID: {prediction.id[:8]}..."

        return f"{line1}\n{line2}"
