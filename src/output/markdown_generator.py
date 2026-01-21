"""Markdown report generation for video documentation."""

from datetime import datetime

from ..models.generation import GenerationContext


def generate_markdown_report(context: GenerationContext) -> str:
    """
    Create markdown report content from generation context.

    Args:
        context: GenerationContext with all generation data

    Returns:
        Formatted markdown report string
    """
    # Prepare duration section based on whether there was adjustment
    duration_section = f"""### Duration
- **Original Frames**: {context.num_frames}"""

    if context.adjustment_info and context.adjustment_info.get("reason"):
        if context.adjustment_info.get("type") == "frames":
            duration_section += f"""
- **Adjusted Frames**: {context.adjustment_info["adjusted"]} (was {context.adjustment_info["original"]})
- **Adjustment Reason**: {context.adjustment_info["reason"]}"""
        elif context.adjustment_info.get("type") == "seconds":
            duration_section += f"""
- **Converted to Seconds**: {context.adjustment_info["original_seconds"]}s (at {context.adjustment_info["fps"]} fps)
- **Adjusted Duration**: {context.adjustment_info["adjusted_seconds"]}s
- **Adjustment Reason**: {context.adjustment_info["reason"]}"""

    # Add FPS info if available
    if context.profile.get("duration_config"):
        duration_section += f"""
- **FPS**: {context.profile["duration_config"]["fps"]}
- **Duration Type**: {context.profile["duration_config"]["duration_type"]}"""

    # Build header with optional project name
    header = f"# Video Generation Report"
    project_name = context.profile.get("project_name")
    if project_name:
        header = f"# {project_name}\n\n## Video Generation Report"

    return f"""{header}

## Generation Details
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Profile**: {context.profile["name"]}
- **Model**: {context.profile["model_id"]}
- **Cost**: ${context.cost:.4f}

## Input Data

### Motion Prompt
```
{context.prompt}
```

### Source Image
- **URL**: {context.image_url}
- **Image URL File**: {context.image_url_file.name}

{duration_section}

## Generation Parameters

### Video Settings
- **Resolution**: {context.params.get("resolution", "NOT SET")}
- **Aspect Ratio**: {context.params.get("aspect_ratio", "NOT SET")}
- **Compression (CRF)**: {context.params.get("constant_rate_factor", "NOT SET")}

### Inference Settings
- **First Pass Steps**: {context.params.get("first_pass_num_inference_steps", "N/A")}
- **First Pass Skip Final**: {context.params.get("first_pass_skip_final_steps", "N/A")}
- **Second Pass Steps**: {context.params.get("second_pass_num_inference_steps", "N/A")}
- **Second Pass Skip Initial**: {context.params.get("second_pass_skip_initial_steps", "N/A")}

### Quality Control
- **Negative Prompt**: {context.params.get("negative_prompt", "none")}
- **Safety Checker**: {context.params.get("enable_safety_checker", "NOT SET")}
- **Expand Prompt**: {context.params.get("expand_prompt", "NOT SET")}

## Output Files
- **Video**: `{context.video_path.name}`
- **Video Size**: {context.video_path.stat().st_size / (1024 * 1024):.2f} MB
- **Video URL**: {context.video_url[:100]}...

## Source Files
- **Prompt**: {context.prompt_file.name}
- **Image URL**: {context.image_url_file.name}
- **Num Frames**: {context.num_frames_file.name}
"""
