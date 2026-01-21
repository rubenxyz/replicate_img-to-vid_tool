"""Hybrid progress implementation using alive-progress with loguru for logging."""

from typing import Optional, Callable, Dict, Any
from contextlib import contextmanager
from loguru import logger

try:
    from alive_progress import alive_bar, config_handler

    ALIVE_PROGRESS_AVAILABLE = True
except ImportError:
    ALIVE_PROGRESS_AVAILABLE = False
    config_handler = None

    def alive_bar(*args, **kwargs):
        class DummyBar:
            def __call__(self, advance=None):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            text = ""

        return DummyBar()


class HybridVideoProgress:
    """
    Hybrid progress using alive-progress for main task + loguru for detailed logging.

    Strategy (per manifesto):
    - alive-progress: Main video generation progress (maximum visual flair)
    - loguru: Detailed sub-operation logging (console output, formatting)

    This gives us:
    - Beautiful animated main progress with dual-line status
    - Detailed loguru-formatted console output for each operation
    - Best of both worlds: visual appeal + professional logging
    """

    def __init__(self):
        """Initialize hybrid progress system."""
        self.bar = None
        self.current_video = None
        self.total_cost = 0.0

    @contextmanager
    def track_generation(self, total_videos: int, title: str = "Video Generation"):
        """
        Track video generation with alive-progress bar + loguru logging.

        Args:
            total_videos: Total number of videos to generate
            title: Progress bar title

        Yields:
            Tuple of (bar,) for updates
        """
        logger.info(f"🎬 {title}")
        logger.info(f"Total videos: {total_videos}")

        # Main progress with alive-progress (maximum visual flair!)
        self.bar = alive_bar(
            total_videos,
            title=f"🎬 {title}",
            bar="smooth",
            spinner="dots_waves",
            dual_line=True,
            unit="videos",
            unit_scale=False,
        )
        try:
            yield self.bar
        finally:
            self.bar = None
            self.current_video = None

    def update_video_status(
        self, video_name: str, phase: str, details: Optional[str] = None
    ) -> None:
        """
        Update current video status with dual-line display.

        Args:
            video_name: Current video name
            phase: Processing phase
            details: Optional additional details
        """
        self.current_video = video_name

        status_line1 = f"→ {video_name}"
        status_line2 = f"   Phase: {phase}"

        if details:
            status_line2 += f" | {details}"

        if self.total_cost > 0:
            status_line2 += f" | Cost: ${self.total_cost:.2f}"

        if self.bar:
            self.bar.text = f"{status_line1}\n{status_line2}"

    def log_phase_start(self, phase: str, details: str) -> None:
        """
        Log phase start with formatting.

        Args:
            phase: Phase name
            details: Phase details
        """
        emoji_map = {
            "Initializing": "🚀",
            "Preparing": "📋",
            "API Call": "📡",
            "Generating": "⚙️",
            "Downloading": "📥",
            "Finalizing": "💾",
        }

        emoji = emoji_map.get(phase, "▶️")
        logger.info(f"{emoji} {phase}: {details}")

    def log_api_status(self, status: str, percentage: Optional[float] = None) -> None:
        """
        Log API status updates.

        Args:
            status: API status
            percentage: Optional percentage complete
        """
        status_emoji = {
            "starting": "🚀",
            "queued": "⏳",
            "processing": "⚙️",
            "succeeded": "✅",
            "failed": "❌",
        }

        emoji = status_emoji.get(status.lower(), "▶️")

        if percentage is not None:
            logger.info(f"  {emoji} API: {status.title()} ({percentage:.0f}%)")
        else:
            logger.info(f"  {emoji} API: {status.title()}")

    def mark_success(self, video_name: str, cost: float) -> None:
        """
        Mark video as successfully completed.

        Args:
            video_name: Video name
            cost: Video generation cost
        """
        self.total_cost += cost

        logger.success(f"✓ {video_name} - ${cost:.2f}")

        if self.bar:
            self.bar()

    def mark_error(self, video_name: str, error_msg: str) -> None:
        """
        Mark video as failed.

        Args:
            video_name: Video name
            error_msg: Error message
        """
        logger.error(f"✗ {video_name}")
        logger.error(f"Error: {error_msg}")

        if self.bar:
            self.bar()

    def print_summary(self, total: int, success: int, total_cost: float) -> None:
        """
        Print final summary.

        Args:
            total: Total videos
            success: Successful videos
            total_cost: Total cost
        """
        logger.info("")

        failed = total - success

        logger.info("📊 Generation Summary")
        logger.info(f"Total Videos: {total}")
        logger.success(f"Successful: {success}")

        if failed > 0:
            logger.error(f"Failed: {failed}")

        logger.info(f"Total Cost: ${total_cost:.2f}")

        if success > 0:
            avg_cost = total_cost / success
            logger.info(f"Avg Cost/Video: ${avg_cost:.2f}")


def create_hybrid_api_callback(
    hybrid: HybridVideoProgress,
) -> Callable[[str, Optional[float]], None]:
    """
    Create API callback for hybrid progress.

    Args:
        hybrid: HybridVideoProgress instance

    Returns:
        Callback function
    """

    def callback(status: str, percentage: Optional[float]):
        """Update progress based on API status."""
        hybrid.log_api_status(status, percentage)

        if hybrid.current_video:
            details = f"API: {status.title()}"
            if percentage is not None:
                details += f" ({percentage:.0f}%)"

            hybrid.update_video_status(hybrid.current_video, "Generating", details)

    return callback


if __name__ == "__main__":
    from time import sleep

    videos = [
        {"name": "video01", "cost": 0.15},
        {"name": "video02", "cost": 0.12},
        {"name": "video03", "cost": 0.18},
    ]

    hybrid = HybridVideoProgress()

    with hybrid.track_generation(len(videos), "Example Generation") as bar:
        for video in videos:
            hybrid.update_video_status(
                video["name"], "Initializing", "Setting up context"
            )
            sleep(0.5)

            hybrid.log_phase_start("Preparing", "Building API parameters")
            sleep(0.5)

            hybrid.update_video_status(
                video["name"], "Generating", "Sending API request"
            )

            hybrid.log_api_status("starting")
            sleep(0.5)
            hybrid.log_api_status("processing", 50)
            sleep(0.5)
            hybrid.log_api_status("processing", 85)
            sleep(0.5)
            hybrid.log_api_status("succeeded", 100)

            hybrid.log_phase_start("Downloading", "Fetching generated video")
            sleep(0.5)

            hybrid.mark_success(video["name"], video["cost"])

        hybrid.print_summary(len(videos), len(videos), sum(v["cost"] for v in videos))
