"""Output generation and documentation for video processing."""
import json
from loguru import logger

from ..models.generation import GenerationContext
from ..output.json_generator import JSONGenerator
from ..output.markdown_generator import MarkdownGenerator
from ..output.log_generator import LogGenerator
from ..output.file_manager import FileManager


def save_generation_files(context: GenerationContext) -> None:
    """
    Save comprehensive documentation for video generation.
    
    Args:
        context: GenerationContext with all required data for output generation
    """
    try:
        # 1. Save the JSON payload
        json_generator = JSONGenerator()
        payload = json_generator.create_payload(
            context.profile, context.image_url, context.prompt, context.params, 
            context.video_url, context.video_path, context.prompt_file, 
            context.image_url_file, context.num_frames_file, context.adjustment_info
        )
        
        json_path = context.output_dir / "generation_payload.json"
        with open(json_path, 'w') as f:
            json.dump(payload, f, indent=2)
        logger.debug(f"Saved JSON payload: {json_path}")
        
        # 2. Create human-readable markdown report
        markdown_generator = MarkdownGenerator()
        markdown_content = markdown_generator.create_report(
            context.profile, context.cost, context.prompt, context.image_url, context.num_frames,
            context.params, context.video_url, context.video_path, context.prompt_file,
            context.image_url_file, context.num_frames_file, context.adjustment_info
        )
        
        markdown_path = context.output_dir / "VIDEO_REPORT.md"
        markdown_path.write_text(markdown_content)
        logger.debug(f"Saved markdown report: {markdown_path}")
        
        # 3. Save verbose log for this specific generation
        log_generator = LogGenerator()
        log_content = log_generator.create_log(
            context.output_dir, context.prompt_file, context.image_url_file, context.num_frames_file,
            context.prompt, context.image_url, context.num_frames, context.profile, context.params,
            context.video_url, context.video_path
        )
        
        log_path = context.output_dir / "generation.log"
        log_path.write_text(log_content)
        logger.debug(f"Saved generation log: {log_path}")
        
        # 4. Copy source files for reference
        file_manager = FileManager()
        file_manager.copy_source_files(
            context.prompt_file, context.image_url_file, context.num_frames_file, context.output_dir
        )
        
        logger.info(f"📝 Saved all documentation files to {context.output_dir}")
        
    except Exception as e:
        logger.warning(f"Failed to save some documentation files: {e}")

