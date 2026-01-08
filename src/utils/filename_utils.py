"""Filename utilities for timestamp handling."""

import re
from datetime import datetime
from pathlib import Path


def generate_video_filename(markdown_filename: str) -> str:
    """
    Generate video filename with timestamp handling.

    Detects and replaces timestamps in both formats:
    - Bracketed: [YYMMDD_HHMMSS] → Replaced with [current_timestamp]
    - Unbracketed: YYMMDD_HHMMSS (as suffix) → Replaced with current_timestamp (no brackets)

    If no timestamp exists, appends current timestamp (no brackets) as suffix.

    Args:
        markdown_filename: Original markdown filename (with or without .md extension)

    Returns:
        Video filename with .mp4 extension and updated/added timestamp

    Examples:
        >>> generate_video_filename("video_[250118_143022].md")
        "video_[250118_150530].mp4"  # bracketed timestamp replaced with bracketed

        >>> generate_video_filename("frame0145-260101_220134.md")
        "frame0145-260108_150530.mp4"  # unbracketed timestamp replaced with unbracketed

        >>> generate_video_filename("my_video.md")
        "my_video_260108_150530.mp4"  # timestamp added as suffix (no brackets)
    """
    # Remove .md extension if present
    stem = Path(markdown_filename).stem

    # Generate current timestamp in YYMMDD_HHMMSS format
    current_timestamp = datetime.now().strftime("%y%m%d_%H%M%S")

    # Pattern 1: Match bracketed timestamp [YYMMDD_HHMMSS]
    bracketed_pattern = r"\[(\d{6}_\d{6})\]"

    # Pattern 2: Match unbracketed timestamp as suffix: -YYMMDD_HHMMSS or _YYMMDD_HHMMSS
    unbracketed_pattern = r"[-_](\d{6}_\d{6})$"

    # Check for bracketed timestamp first
    match_bracketed = re.search(bracketed_pattern, stem)
    if match_bracketed:
        # Replace existing bracketed timestamp with current one (keep brackets)
        new_stem = re.sub(bracketed_pattern, f"[{current_timestamp}]", stem)
        return f"{new_stem}.mp4"

    # Check for unbracketed timestamp
    match_unbracketed = re.search(unbracketed_pattern, stem)
    if match_unbracketed:
        # Replace unbracketed timestamp with current one (no brackets)
        new_stem = re.sub(unbracketed_pattern, f"-{current_timestamp}", stem)
        return f"{new_stem}.mp4"

    # No timestamp found, add as suffix (no brackets)
    new_stem = f"{stem}_{current_timestamp}"
    return f"{new_stem}.mp4"


def extract_timestamp_from_filename(filename: str) -> str | None:
    """
    Extract timestamp from filename if present (both bracketed and unbracketed).

    Args:
        filename: Filename to extract timestamp from

    Returns:
        Timestamp string (YYMMDD_HHMMSS) or None if not found

    Examples:
        >>> extract_timestamp_from_filename("video_[250118_143022].md")
        "250118_143022"

        >>> extract_timestamp_from_filename("frame0145-260101_220134.md")
        "260101_220134"

        >>> extract_timestamp_from_filename("video.md")
        None
    """
    # Try bracketed format first
    bracketed_pattern = r"\[(\d{6}_\d{6})\]"
    match = re.search(bracketed_pattern, filename)
    if match:
        return match.group(1)

    # Try unbracketed format (suffix after dash or underscore)
    unbracketed_pattern = r"[-_](\d{6}_\d{6})(?:\.|$)"
    match = re.search(unbracketed_pattern, filename)
    if match:
        return match.group(1)

    return None
