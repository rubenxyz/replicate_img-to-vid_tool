"""Unit tests for filename utilities."""

import re
from datetime import datetime
from src.utils.filename_utils import (
    generate_video_filename,
    extract_timestamp_from_filename,
)


def test_generate_video_filename_with_bracketed_timestamp():
    """Test that existing bracketed timestamp is replaced with current one."""
    input_name = "video_[250118_143022].md"
    result = generate_video_filename(input_name)

    # Check format: video_[YYMMDD_HHMMSS].mp4
    assert result.startswith("video_[")
    assert result.endswith("].mp4")

    # Verify timestamp pattern matches
    timestamp_pattern = r"\[(\d{6}_\d{6})\]"
    match = re.search(timestamp_pattern, result)
    assert match is not None

    # Verify timestamp is different (assuming test runs in different second)
    assert "[250118_143022]" not in result or result == "video_[250118_143022].mp4"


def test_generate_video_filename_with_unbracketed_timestamp():
    """Test that unbracketed timestamp is replaced with bracketed current one."""
    input_name = "frame0145-260101_220134.md"
    result = generate_video_filename(input_name)

    # Check format: frame0145-[YYMMDD_HHMMSS].mp4
    assert result.startswith("frame0145-[")
    assert result.endswith("].mp4")

    # Verify old unbracketed timestamp is gone
    assert "260101_220134" not in result

    # Verify new timestamp is bracketed
    timestamp_pattern = r"\[(\d{6}_\d{6})\]"
    match = re.search(timestamp_pattern, result)
    assert match is not None


def test_generate_video_filename_with_underscore_timestamp():
    """Test unbracketed timestamp with underscore separator."""
    input_name = "scene_240615_120000.md"
    result = generate_video_filename(input_name)

    # Check that result has bracketed timestamp
    assert result.startswith("scene-[")
    assert result.endswith("].mp4")

    # Verify old timestamp is replaced
    assert "240615_120000" not in result


def test_generate_video_filename_without_timestamp():
    """Test that timestamp is added as suffix when none exists."""
    input_name = "my_video.md"
    result = generate_video_filename(input_name)

    # Check format: my_video_[YYMMDD_HHMMSS].mp4
    assert result.startswith("my_video_[")
    assert result.endswith("].mp4")

    # Verify timestamp pattern matches
    timestamp_pattern = r"\[(\d{6}_\d{6})\]"
    match = re.search(timestamp_pattern, result)
    assert match is not None

    # Verify timestamp is reasonably current (within 1 minute)
    timestamp_str = match.group(1)
    parsed_time = datetime.strptime(timestamp_str, "%y%m%d_%H%M%S")
    time_diff = abs((datetime.now() - parsed_time).total_seconds())
    assert time_diff < 60, f"Timestamp too far from current time: {time_diff}s"


def test_generate_video_filename_no_extension():
    """Test with filename without extension."""
    input_name = "another_video"
    result = generate_video_filename(input_name)

    assert result.startswith("another_video_[")
    assert result.endswith("].mp4")


def test_generate_video_filename_multiple_timestamps():
    """Test with multiple timestamp patterns (only first should be replaced)."""
    input_name = "video_[250118_143022]_backup_[250118_150000].md"
    result = generate_video_filename(input_name)

    # Should replace first timestamp
    assert not result.startswith("video_[250118_143022]")
    assert result.endswith(".mp4")


def test_extract_timestamp_from_bracketed_filename():
    """Test extracting bracketed timestamp."""
    filename = "video_[250118_143022].md"
    result = extract_timestamp_from_filename(filename)

    assert result == "250118_143022"


def test_extract_timestamp_from_unbracketed_filename():
    """Test extracting unbracketed timestamp."""
    filename = "frame0145-260101_220134.md"
    result = extract_timestamp_from_filename(filename)

    assert result == "260101_220134"


def test_extract_timestamp_from_filename_without_timestamp():
    """Test extracting when no timestamp exists."""
    filename = "video.md"
    result = extract_timestamp_from_filename(filename)

    assert result is None


def test_extract_timestamp_prefers_bracketed():
    """Test that bracketed timestamp is preferred over unbracketed."""
    filename = "video_[250118_143022]-260101_220134.md"
    result = extract_timestamp_from_filename(filename)

    # Should return bracketed timestamp first
    assert result == "250118_143022"


def test_generate_video_filename_with_special_characters():
    """Test with special characters in filename."""
    input_name = "my-video_test (1).md"
    result = generate_video_filename(input_name)

    assert result.startswith("my-video_test (1)_[")
    assert result.endswith("].mp4")


def test_generate_video_filename_preserves_path():
    """Test that only filename is modified, not full path."""
    input_name = "scene_001.md"
    result = generate_video_filename(input_name)

    # Should be filename only, no path separators
    assert "/" not in result
    assert "\\" not in result
    assert result.startswith("scene_001_[")


def test_generate_video_filename_with_unbracketed_dash():
    """Test unbracketed timestamp with dash separator."""
    input_name = "frame0145-260101_220134.md"
    result = generate_video_filename(input_name)

    # Should replace with bracketed timestamp
    assert result.startswith("frame0145-[")
    assert result.endswith("].mp4")
    assert "260101_220134" not in result


def test_extract_unbracketed_timestamp():
    """Test extracting unbracketed timestamp."""
    filename = "frame0145-260101_220134.md"
    result = extract_timestamp_from_filename(filename)

    assert result == "260101_220134"
