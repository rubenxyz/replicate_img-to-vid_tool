"""Main entry point for image-to-video generation."""

import sys
from loguru import logger
from pathlib import Path
from typing import Dict, Any, List, Optional

from .utils.epic_progress import ProgressBar
from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.processor import process_matrix
from .processing.profile_loader import load_active_profiles
from .models.processing import ProcessingContext
from .models.video_processing import APIClientConfig
from .output.reporter import create_success_report, create_cost_report

# Lazy import for adjustments_reporter - only loaded when needed
from .utils.logging import setup_logging
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import validate_environment, validate_input_directories
from .exceptions import VideoGenerationError, AuthenticationError, InputValidationError
from .utils.verbose_output import show_project_header


def _process_and_report(
    client: ReplicateClient, active_profiles: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Execute processing and generate reports."""
    logger.info("Starting video generation matrix processing")

    with ProgressBar() as progress:
        context = ProcessingContext(
            client=client,
            input_dir=INPUT_DIR,
            profiles_dir=PROFILES_DIR,
            output_dir=OUTPUT_DIR,
            progress=progress,
        )
        return process_matrix(context)


def _extract_project_name(profiles: List[Dict[str, Any]]) -> str | None:
    """Extract a single project name from profiles, or None if multiple or none."""
    project_names = set()
    for profile in profiles:
        project_name = profile.get("project_name")
        if project_name:
            project_names.add(project_name)

    if len(project_names) == 1:
        return project_names.pop()
    return None


def main() -> int:
    """Main entry point for image-to-video generation."""

    try:
        api_key = validate_environment()
        validate_input_directories(INPUT_DIR, PROFILES_DIR)

        active_profiles = load_active_profiles(PROFILES_DIR)
        project_name = _extract_project_name(active_profiles)

        # Setup logging after we know the project name
        setup_logging(project_name=project_name)
        show_project_header(active_profiles)

        config = APIClientConfig(api_token=api_key)
        client = ReplicateClient(config=config)

        results = _process_and_report(client, active_profiles)
        if results is None:
            return 1

        output_dir = results["output_dir"]
        create_success_report(results, output_dir)
        create_cost_report(results, output_dir)

        if results.get("adjustments"):
            from .reporting.adjustments_reporter import create_adjustments_report

            create_adjustments_report(
                adjustments=results["adjustments"],
                output_dir=output_dir,
                total_processed=results["total"],
            )

        logger.success(f"✅ Completed: {results['success']}/{results['total']} videos")
        logger.info(f"Total cost: ${results['cost']:.2f}")
        logger.info(f"Output directory: {output_dir}")

        try:
            archive_and_cleanup_logs(output_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup logs (non-fatal): {e}")

        return 0

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return 2
    except InputValidationError as e:
        logger.error(f"Input validation failed: {e}")
        return 3
    except VideoGenerationError as e:
        logger.error(f"Video generation error: {e}")
        return 4
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
