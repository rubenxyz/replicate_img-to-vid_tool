"""Unit tests for cleanup utilities."""

import subprocess
from pathlib import Path
from zipfile import ZipFile
import pytest
from src.utils.cleanup import archive_and_cleanup_logs, _trash_files


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory with sample files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create sample files
    (output_dir / "video1.mp4").write_text("fake video 1")
    (output_dir / "video1.json").write_text('{"test": "data"}')
    (output_dir / "video1.md").write_text("# Test Report")
    (output_dir / "video1.log").write_text("log content")

    (output_dir / "video2.mp4").write_text("fake video 2")
    (output_dir / "video2.json").write_text('{"test": "data"}')

    (output_dir / "SUCCESS.md").write_text("# Success")
    (output_dir / "cost_report.md").write_text("# Costs")

    return output_dir


def test_archive_creates_zip_with_non_mp4_files(temp_output_dir):
    """Test that archive creates a zip file containing all non-MP4 files."""
    # Run cleanup
    archive_and_cleanup_logs(temp_output_dir)

    # Find the created zip file
    zip_files = list(temp_output_dir.glob("*_logs.zip"))
    assert len(zip_files) == 1, "Should create exactly one zip file"

    zip_path = zip_files[0]

    # Verify zip contains the right files
    with ZipFile(zip_path, 'r') as zipf:
        files_in_zip = set(zipf.namelist())

    expected_files = {
        "video1.json",
        "video1.md",
        "video1.log",
        "video2.json",
        "SUCCESS.md",
        "cost_report.md"
    }

    assert files_in_zip == expected_files


def test_archive_keeps_mp4_files(temp_output_dir):
    """Test that MP4 files are kept in the output directory."""
    # Run cleanup
    archive_and_cleanup_logs(temp_output_dir)

    # Verify MP4 files still exist
    mp4_files = list(temp_output_dir.glob("*.mp4"))
    assert len(mp4_files) == 2
    assert (temp_output_dir / "video1.mp4").exists()
    assert (temp_output_dir / "video2.mp4").exists()


def test_archive_handles_empty_directory(tmp_path):
    """Test that archive handles directory with no files gracefully."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # Should not raise an error
    archive_and_cleanup_logs(empty_dir)

    # Should not create any zip files
    zip_files = list(empty_dir.glob("*.zip"))
    assert len(zip_files) == 0


def test_archive_handles_only_mp4_files(tmp_path):
    """Test that archive handles directory with only MP4 files."""
    output_dir = tmp_path / "videos_only"
    output_dir.mkdir()

    (output_dir / "video1.mp4").write_text("fake video")
    (output_dir / "video2.mp4").write_text("fake video")

    # Should not raise an error
    archive_and_cleanup_logs(output_dir)

    # Should not create any zip files
    zip_files = list(output_dir.glob("*.zip"))
    assert len(zip_files) == 0


def test_archive_handles_nested_files(tmp_path):
    """Test that archive handles nested directory structure."""
    output_dir = tmp_path / "nested"
    output_dir.mkdir()

    # Create nested structure
    subdir = output_dir / "subdir"
    subdir.mkdir()

    (output_dir / "video.mp4").write_text("video")
    (output_dir / "report.md").write_text("report")
    (subdir / "nested.log").write_text("nested log")

    # Run cleanup
    archive_and_cleanup_logs(output_dir)

    # Verify zip contains files with relative paths
    zip_files = list(output_dir.glob("*_logs.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0], 'r') as zipf:
        files_in_zip = set(zipf.namelist())

    assert "report.md" in files_in_zip
    assert "subdir/nested.log" in files_in_zip


def test_archive_nonexistent_directory(tmp_path):
    """Test that archive handles nonexistent directory gracefully."""
    nonexistent = tmp_path / "does_not_exist"

    # Should not raise an error
    archive_and_cleanup_logs(nonexistent)


def test_trash_files_requires_trash_command(tmp_path, monkeypatch):
    """Test that _trash_files raises error if trash command is not available."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    # Mock subprocess.run to simulate trash command not found
    def mock_run(cmd, **kwargs):
        if cmd == ["which", "trash"]:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(FileNotFoundError, match="trash command not found"):
        _trash_files([test_file])
