"""Unit tests for path validation utility."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

from src.utils.path_validator import validate_custom_path, validate_custom_paths


class TestValidateCustomPath:
    """Tests for validate_custom_path function."""

    def test_valid_input_directory(self):
        """Test that valid input directory passes validation."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)
            # Should not raise
            validate_custom_path(input_path, "input")

    def test_valid_output_directory(self):
        """Test that valid output directory passes validation."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            # Should not raise
            validate_custom_path(output_path, "output")

    def test_nonexistent_input_directory(self):
        """Test that non-existent input directory raises FileNotFoundError."""
        nonexistent_path = Path("/tmp/this/path/does/not/exist/12345")
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_custom_path(nonexistent_path, "input")
        assert "input" in str(exc_info.value).lower()

    def test_nonexistent_output_directory(self):
        """Test that non-existent output directory raises FileNotFoundError."""
        nonexistent_path = Path("/tmp/this/path/does/not/exist/67890")
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_custom_path(nonexistent_path, "output")
        assert "output" in str(exc_info.value).lower()

    def test_file_instead_of_directory(self):
        """Test that a file path raises NotADirectoryError."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "testfile.txt"
            file_path.write_text("test")
            with pytest.raises(NotADirectoryError) as exc_info:
                validate_custom_path(file_path, "input")
            assert "not a directory" in str(exc_info.value).lower()


class TestValidateCustomPaths:
    """Tests for validate_custom_paths function."""

    def test_both_paths_valid(self):
        """Test that valid input and output paths pass."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input"
            output_path = Path(tmpdir) / "output"
            input_path.mkdir()
            output_path.mkdir()
            # Should not raise
            validate_custom_paths(input_path, output_path)

    def test_only_input_path_valid(self):
        """Test that only input path specified passes."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input"
            input_path.mkdir()
            # Should not raise with None for output
            validate_custom_paths(input_path, None)

    def test_only_output_path_valid(self):
        """Test that only output path specified passes."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()
            # Should not raise with None for input
            validate_custom_paths(None, output_path)

    def test_both_paths_none(self):
        """Test that None for both paths passes (no validation needed)."""
        # Should not raise
        validate_custom_paths(None, None)

    def test_invalid_input_path_raises(self):
        """Test that invalid input path raises error even with valid output."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()
            invalid_input = Path("/tmp/nonexistent/12345")
            with pytest.raises(FileNotFoundError):
                validate_custom_paths(invalid_input, output_path)

    def test_invalid_output_path_raises(self):
        """Test that invalid output path raises error even with valid input."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input"
            input_path.mkdir()
            invalid_output = Path("/tmp/nonexistent/67890")
            with pytest.raises(FileNotFoundError):
                validate_custom_paths(input_path, invalid_output)
