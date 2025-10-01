"""Main entry point with verbose output enabled by default."""
import sys
from loguru import logger

from .api.client import ReplicateClient
from .config.settings import (
    PROMPT_DIR, IMAGE_URL_DIR, NUM_FRAMES_DIR, 
    PROFILES_DIR, OUTPUT_DIR
)
from .processing.verbose_processor import process_matrix_verbose
from .models.processing import ProcessingContext
from .output.reporter import create_success_report, create_cost_report
# Lazy import for adjustments_reporter - only loaded when needed
from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .validation.environment import validate_environment, validate_input_directories
from .exceptions import (
    VideoGenerationError, AuthenticationError, InputValidationError
)


def main() -> int:
    """Main entry point with verbose terminal output."""
    
    # Setup dual logging (file + console)
    setup_dual_logging(enable_verbose=True)
    
    try:
        # Validate environment
        log_stage_emoji("starting", "Validating environment and authentication...")
        api_key = validate_environment()
        logger.success("Authentication successful")
        
        # Validate input directories
        log_stage_emoji("preparing", "Validating input directories...")
        validate_input_directories(
            PROMPT_DIR, IMAGE_URL_DIR, NUM_FRAMES_DIR, PROFILES_DIR
        )
        logger.success("All input directories validated")
        
        # Initialize client
        client = ReplicateClient(api_token=api_key)
        
        # Create processing context
        context = ProcessingContext(
            client=client,
            prompt_dir=PROMPT_DIR,
            image_url_dir=IMAGE_URL_DIR,
            num_frames_dir=NUM_FRAMES_DIR,
            profiles_dir=PROFILES_DIR,
            output_dir=OUTPUT_DIR,
            progress=None  # Verbose processor creates its own
        )
        
        # Process with verbose output
        log_stage_emoji("processing", "Starting video generation matrix...")
        results = process_matrix_verbose(context)
        
        # Generate reports
        log_stage_emoji("saving", "Generating reports...")
        output_dir = results['output_dir']
        create_success_report(results, output_dir)
        create_cost_report(results, output_dir)
        
        # Create adjustments report if needed (lazy load)
        if results.get('adjustments'):
            from .reporting.adjustments_reporter import create_adjustments_report
            create_adjustments_report(
                adjustments=results['adjustments'],
                output_dir=output_dir,
                total_processed=results['total']
            )
            logger.info(f"⚠️ {len(results['adjustments'])} duration adjustments made")
        
        # Final summary
        logger.success("═" * 60)
        log_stage_emoji("complete", f"All processing complete!")
        logger.success(f"✅ Success: {results['success']}/{results['total']} videos")
        logger.info(f"💰 Total cost: ${results['cost']:.2f}")
        logger.info(f"📁 Output: {output_dir}")
        logger.success("═" * 60)
        
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