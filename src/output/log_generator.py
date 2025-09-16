"""Log file generation for video documentation."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class LogGenerator:
    """Generator for verbose log files."""
    
    @staticmethod
    def create_log(output_dir: Path, prompt_file: Path, image_url_file: Path,
                  num_frames_file: Path, prompt: str, image_url: str,
                  num_frames: int, profile: Dict[str, Any], params: Dict[str, Any],
                  video_url: str, video_path: Path) -> str:
        """
        Create verbose generation log.
        
        Args:
            output_dir: Output directory path
            prompt_file: Path to prompt file
            image_url_file: Path to image URL file
            num_frames_file: Path to num frames file
            prompt: Motion prompt text
            image_url: Source image URL
            num_frames: Number of frames
            profile: Profile configuration dictionary
            params: Generation parameters
            video_url: Generated video URL
            video_path: Local video file path
            
        Returns:
            Formatted log string
        """
        return f"""════════════════════════════════════════════════════════════════════════
VIDEO GENERATION LOG
════════════════════════════════════════════════════════════════════════
Timestamp: {datetime.now().isoformat()}
Directory: {output_dir}

INPUT FILES:
- Prompt: {prompt_file}
- Image URL: {image_url_file}
- Num Frames: {num_frames_file}

EXTRACTED DATA:
- Prompt Text: {prompt}
- Image URL: {image_url}
- Frame Count: {num_frames}

PROFILE CONFIGURATION:
{json.dumps(profile, indent=2)}

API PAYLOAD:
{json.dumps({"image_url": image_url, "prompt": prompt, **params}, indent=2)}

API RESPONSE:
- Video URL: {video_url}
- Download Success: True
- Local Path: {video_path}
- File Size: {video_path.stat().st_size} bytes

GENERATION COMPLETE
════════════════════════════════════════════════════════════════════════
"""