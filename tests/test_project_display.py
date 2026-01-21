"""Tests for project name display in outputs."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from src.utils.verbose_output import show_project_header
from src.utils.logging import _sanitize_for_filename
from src.output.markdown_generator import generate_markdown_report


class TestProjectHeader:
    """Tests for project header display."""

    def test_single_profile_with_project_name(self):
        """Test header with single profile containing project name."""
        profiles = [{"project_name": "Test Project"}]
        # Should not raise
        show_project_header(profiles)

    def test_multiple_profiles_same_name(self):
        """Test header with multiple profiles having same project name."""
        profiles = [
            {"project_name": "Shared Project"},
            {"project_name": "Shared Project"},
        ]
        # Should not raise - deduped to single name
        show_project_header(profiles)

    def test_multiple_profiles_different_names(self):
        """Test header with multiple profiles having different project names."""
        profiles = [
            {"project_name": "Project A"},
            {"project_name": "Project B"},
        ]
        # Should not raise - shows both names
        show_project_header(profiles)

    def test_no_project_names(self):
        """Test header with profiles having no project names."""
        profiles = [{"name": "profile1"}, {"name": "profile2"}]
        # Should not raise - no output
        show_project_header(profiles)

    def test_mixed_profiles_with_without_names(self):
        """Test header with mix of profiles with and without names."""
        profiles = [
            {"project_name": "Named Project"},
            {"name": "unnamed_profile"},
        ]
        # Should not raise - shows only named project
        show_project_header(profiles)


class TestSanitizeForFilename:
    """Tests for filename sanitization."""

    def test_sanitizes_spaces(self):
        """Test that spaces are sanitized."""
        result = _sanitize_for_filename("My Project Name")
        assert " " not in result

    def test_sanitizes_special_chars(self):
        """Test that special characters are sanitized."""
        result = _sanitize_for_filename("Project: Test/Example")
        assert ":" not in result
        assert "/" not in result

    def test_preserves_alphanumeric_and_hyphen_underscore(self):
        """Test that alphanumeric, hyphens, and underscores are preserved."""
        result = _sanitize_for_filename("Project_Name-123")
        assert result == "Project_Name-123"

    def test_empty_string(self):
        """Test empty string handling."""
        result = _sanitize_for_filename("")
        assert result == ""


class TestProjectNameInReports:
    """Tests for project name inclusion in reports."""

    def test_report_with_project_name(self):
        """Test that report includes project name when set."""
        from src.models.generation import GenerationContext

        context = Mock(spec=GenerationContext)
        context.profile = {
            "name": "test_profile",
            "model_id": "test/model",
            "project_name": "WALTZ WITH BASHIR",
            "duration_config": {"fps": 24, "duration_type": "frames"},
        }
        context.prompt = "Test prompt"
        context.image_url = "http://example.com/image.jpg"
        context.image_url_file = Path("/test/image.md")
        context.num_frames = 30
        context.params = {"resolution": "720p"}
        context.video_path = Path("/test/video.mp4")
        context.video_url = "http://example.com/video.mp4"
        context.video_path.stat.return_value.st_size = 1024000
        context.cost = 0.05
        context.adjustment_info = None
        context.prompt_file = Path("/test/prompt.md")
        context.num_frames_file = Path("/test/frames.md")

        report = generate_markdown_report(context)
        assert "# WALTZ WITH BASHIR" in report
        assert "## Video Generation Report" in report

    def test_report_without_project_name(self):
        """Test that report works without project name (backward compatibility)."""
        from src.models.generation import GenerationContext

        context = Mock(spec=GenerationContext)
        context.profile = {
            "name": "test_profile",
            "model_id": "test/model",
            "duration_config": {"fps": 24, "duration_type": "frames"},
        }
        context.prompt = "Test prompt"
        context.image_url = "http://example.com/image.jpg"
        context.image_url_file = Path("/test/image.md")
        context.num_frames = 30
        context.params = {"resolution": "720p"}
        context.video_path = Path("/test/video.mp4")
        context.video_url = "http://example.com/video.mp4"
        context.video_path.stat.return_value.st_size = 1024000
        context.cost = 0.05
        context.adjustment_info = None
        context.prompt_file = Path("/test/prompt.md")
        context.num_frames_file = Path("/test/frames.md")

        report = generate_markdown_report(context)
        assert "# Video Generation Report" in report
        assert "WALTZ WITH BASHIR" not in report
