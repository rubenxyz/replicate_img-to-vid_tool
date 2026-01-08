"""Main entry point for image-to-video generation."""

import sys
from loguru import logger
from rich.progress import Progress

from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.processor import process_matrix
from .models.processing import ProcessingContext
from .output.reporter import create_success_report, create_cost_report

# Lazy import for adjustments_reporter - only loaded when needed
from .utils.logging import setup_logging
from .validation.environment import validate_environment, validate_input_directories
from .exceptions import VideoGenerationError, AuthenticationError, InputValidationError


def main() -> int:
    """Main entry point for image-to-video generation."""

    # Setup logging
    setup_logging()

    try:
        # Validate environment and authenticate
        api_key = validate_environment()

        # Validate input directories
        validate_input_directories(INPUT_DIR, PROFILES_DIR)

        # Initialize client
        client = ReplicateClient(api_token=api_key)

        # Process matrix with progress bar
        logger.info("Starting video generation matrix processing")

        with Progress() as progress:
            # Create processing context
            context = ProcessingContext(
                client=client,
                input_dir=INPUT_DIR,
                profiles_dir=PROFILES_DIR,
                output_dir=OUTPUT_DIR,
                progress=progress,
            )

            # Process the matrix
            results = process_matrix(context)

        # Generate reports
        output_dir = results["output_dir"]
        create_success_report(results, output_dir)
        create_cost_report(results, output_dir)

        # Create adjustments report if there were any (lazy load)
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
