"""Log file generation for video documentation."""

import json
from datetime import datetime

from ..models.generation import GenerationContext


def generate_log_content(context: GenerationContext) -> str:
    """
    Create verbose generation log from generation context.

    Args:
        context: GenerationContext with all generation data

    Returns:
        Formatted log string
    """
    return f"""════════════════════════════════════════════════════════════════════════
VIDEO GENERATION LOG
════════════════════════════════════════════════════════════════════════
Timestamp: {datetime.now().isoformat()}
Directory: {context.output_dir}

INPUT FILES:
- Prompt: {context.prompt_file}
- Image URL: {context.image_url_file}
- Num Frames: {context.num_frames_file}

EXTRACTED DATA:
- Prompt Text: {context.prompt}
- Image URL: {context.image_url}
- Frame Count: {context.num_frames}

PROFILE CONFIGURATION:
{json.dumps(context.profile, indent=2)}

API PAYLOAD:
{json.dumps({"image_url": context.image_url, "prompt": context.prompt, **context.params}, indent=2)}

API RESPONSE:
- Video URL: {context.video_url}
- Download Success: True
- Local Path: {context.video_path}
- File Size: {context.video_path.stat().st_size} bytes

GENERATION COMPLETE
════════════════════════════════════════════════════════════════════════
"""
