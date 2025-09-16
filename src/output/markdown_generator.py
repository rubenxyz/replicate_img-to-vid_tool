"""Markdown report generation for video documentation."""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class MarkdownGenerator:
    """Generator for markdown reports."""
    
    @staticmethod
    def create_report(profile: Dict[str, Any], cost: float, prompt: str,
                     image_url: str, num_frames: int, params: Dict[str, Any],
                     video_url: str, video_path: Path, prompt_file: Path,
                     image_url_file: Path, num_frames_file: Path,
                     adjustment_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create markdown report content.
        
        Args:
            profile: Profile configuration dictionary
            cost: Generation cost in USD
            prompt: Motion prompt text
            image_url: Source image URL
            num_frames: Number of frames
            params: Generation parameters
            video_url: Generated video URL
            video_path: Local video file path
            prompt_file: Path to prompt file
            image_url_file: Path to image URL file
            num_frames_file: Path to num frames file
            adjustment_info: Optional duration adjustment information
            
        Returns:
            Formatted markdown report string
        """
        # Prepare duration section based on whether there was adjustment
        duration_section = f"""### Duration
- **Original Frames**: {num_frames}"""
        
        if adjustment_info and adjustment_info.get('reason'):
            if adjustment_info.get('type') == 'frames':
                duration_section += f"""
- **Adjusted Frames**: {adjustment_info['adjusted']} (was {adjustment_info['original']})
- **Adjustment Reason**: {adjustment_info['reason']}"""
            elif adjustment_info.get('type') == 'seconds':
                duration_section += f"""
- **Converted to Seconds**: {adjustment_info['original_seconds']}s (at {adjustment_info['fps']} fps)
- **Adjusted Duration**: {adjustment_info['adjusted_seconds']}s
- **Adjustment Reason**: {adjustment_info['reason']}"""
        
        # Add FPS info if available
        if profile.get('duration_config'):
            duration_section += f"""
- **FPS**: {profile['duration_config']['fps']}
- **Duration Type**: {profile['duration_config']['duration_type']}"""
        
        return f"""# Video Generation Report

## Generation Details
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Profile**: {profile['name']}
- **Model**: {profile['model_id']}
- **Cost**: ${cost:.4f}

## Input Data

### Motion Prompt
```
{prompt}
```

### Source Image
- **URL**: {image_url}
- **Image URL File**: {image_url_file.name}

{duration_section}

## Generation Parameters

### Video Settings
- **Resolution**: {params.get('resolution', 'NOT SET')}
- **Aspect Ratio**: {params.get('aspect_ratio', 'NOT SET')}
- **Compression (CRF)**: {params.get('constant_rate_factor', 'NOT SET')}

### Inference Settings
- **First Pass Steps**: {params.get('first_pass_num_inference_steps', 'N/A')}
- **First Pass Skip Final**: {params.get('first_pass_skip_final_steps', 'N/A')}
- **Second Pass Steps**: {params.get('second_pass_num_inference_steps', 'N/A')}
- **Second Pass Skip Initial**: {params.get('second_pass_skip_initial_steps', 'N/A')}

### Quality Control
- **Negative Prompt**: {params.get('negative_prompt', 'none')}
- **Safety Checker**: {params.get('enable_safety_checker', 'NOT SET')}
- **Expand Prompt**: {params.get('expand_prompt', 'NOT SET')}

## Output Files
- **Video**: `{video_path.name}`
- **Video Size**: {video_path.stat().st_size / (1024*1024):.2f} MB
- **Video URL**: {video_url[:100]}...

## Source Files
- **Prompt**: {prompt_file.name}
- **Image URL**: {image_url_file.name}
- **Num Frames**: {num_frames_file.name}
"""