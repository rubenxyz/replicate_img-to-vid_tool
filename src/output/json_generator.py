"""JSON payload generation for video documentation."""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class JSONGenerator:
    """Generator for JSON payloads and documentation."""
    
    @staticmethod
    def create_payload(profile: Dict[str, Any], image_url: str, prompt: str,
                      params: Dict[str, Any], video_url: str, video_path: Path,
                      prompt_file: Path, image_url_file: Path, 
                      num_frames_file: Path, adjustment_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create JSON payload for documentation.
        
        Args:
            profile: Profile configuration dictionary
            image_url: Source image URL
            prompt: Motion prompt text
            params: Generation parameters
            video_url: Generated video URL
            video_path: Local video file path
            prompt_file: Path to prompt file
            image_url_file: Path to image URL file
            num_frames_file: Path to num frames file
            adjustment_info: Optional duration adjustment information
            
        Returns:
            Dictionary containing complete generation payload
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "model": profile['model_id'],
            "profile_name": profile['name'],
            "duration_config": profile.get('duration_config', {}),
            "request": {
                "image_url": image_url,
                "prompt": prompt,
                **params
            },
            "response": {
                "video_url": video_url,
                "local_path": str(video_path)
            },
            "source_files": {
                "prompt_file": str(prompt_file),
                "image_url_file": str(image_url_file),
                "num_frames_file": str(num_frames_file)
            }
        }
        
        # Add adjustment info if present
        if adjustment_info and adjustment_info.get('reason'):
            payload['duration_adjustment'] = adjustment_info
        
        return payload