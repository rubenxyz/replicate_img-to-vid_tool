"""Main entry point with HYBRID progress (alive-progress WAVES + Rich logging)."""

import sys
from loguru import logger

from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.hybrid_processor import process_matrix_hybrid
from .models.processing import ProcessingContext
from .models.video_processing import APIClientConfig
from .output.reporter import create_success_report, create_cost_report
from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .validation.environment import validate_environment, validate_input_directories
from .exceptions import VideoGenerationError, AuthenticationError, InputValidationError


def main() -> int:
    """
    Main entry point with HYBRID progress (manifesto recommended approach).

    Uses BOTH libraries as recommended:
    - alive-progress: Main task with WAVES animation (maximum visual flair!)
    - Rich: Detailed sub-operation logging (professional formatting)
    """

    # Setup dual logging (file + console)
    setup_dual_logging(enable_verbose=True)

    try:
        # Validate environment
        log_stage_emoji(
            "starting", "🌊 Initializing HYBRID mode (alive-progress WAVES + Rich)"
        )
        api_key = validate_environment()
        logger.success("Authentication successful")

        # Validate input directories
        log_stage_emoji("preparing", "Validating input directories...")
        validate_input_directories(INPUT_DIR, PROFILES_DIR)
        logger.success("All input directories validated")

        # Initialize client with config
        config = APIClientConfig(api_token=api_key)
        client = ReplicateClient(config=config)

        # Create processing context
        context = ProcessingContext(
            client=client,
            input_dir=INPUT_DIR,
            profiles_dir=PROFILES_DIR,
            output_dir=OUTPUT_DIR,
            progress=None,  # Hybrid processor creates its own
        )

        # Process with HYBRID progress (alive WAVES + Rich logging)
        logger.info("═" * 70)
        logger.info("🌊 HYBRID MODE: alive-progress WAVES + Rich Console Logging")
        logger.info("═" * 70)

        results = process_matrix_hybrid(context)

        # Generate reports
        log_stage_emoji("saving", "Generating reports...")
        output_dir = results["output_dir"]
        create_success_report(results, output_dir)
        create_cost_report(results, output_dir)

        # Create adjustments report if needed (lazy load)
        if results.get("adjustments"):
            from .reporting.adjustments_reporter import create_adjustments_report

            create_adjustments_report(
                adjustments=results["adjustments"],
                output_dir=output_dir,
                total_processed=results["total"],
            )
            logger.info(f"⚠️ {len(results['adjustments'])} duration adjustments made")

        # Final summary (already printed by hybrid processor)
        logger.info("═" * 70)
        logger.success(f"✅ Total cost: ${results['cost']:.2f}")
        logger.info(f"📁 Output: {output_dir}")
        logger.info("═" * 70)

        return 0

    except KeyboardInterrupt:
        log_stage_emoji("failed", "Interrupted by user")
        return 130
    except AuthenticationError as e:
        log_stage_emoji("failed", f"Authentication failed: {e}")
        return 2
    except InputValidationError as e:
        log_stage_emoji("failed", f"Input validation failed: {e}")
        return 3
    except VideoGenerationError as e:
        log_stage_emoji("failed", f"Video generation error: {e}")
        logger.exception("Full traceback:")
        return 4
    except Exception as e:
        log_stage_emoji("failed", f"Fatal error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
