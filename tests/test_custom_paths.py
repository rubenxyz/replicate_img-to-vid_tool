"""Integration tests for custom path configuration."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from src.processing.profile_loader import load_single_profile


class TestCustomPathConfiguration:
    """Tests for custom path configuration in profiles."""

    def test_profile_with_project_name(self):
        """Test loading profile with project name."""
        with TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "test_profile.yaml"
            yaml_file.write_text("""
project:
  name: "Test Project"

Model:
  endpoint: test/model
  code-nickname: test

pricing:
  cost_per_frame: 0.01

duration_type: frames
fps: 24
duration_min: 1
duration_max: 100
duration_param_name: num_frames

params:
  resolution: "720p"
""")

            profile = load_single_profile(yaml_file)
            assert profile["project_name"] == "Test Project"
            assert profile["custom_input_path"] is None
            assert profile["custom_output_path"] is None

    def test_profile_with_custom_paths(self):
        """Test loading profile with custom input and output paths."""
        with TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "test_profile.yaml"
            yaml_file.write_text("""
Model:
  endpoint: test/model
  code-nickname: test

pricing:
  cost_per_frame: 0.01

paths:
  input: /custom/input/path
  output: /custom/output/path

duration_type: frames
fps: 24
duration_min: 1
duration_max: 100
duration_param_name: num_frames

params:
  resolution: "720p"
""")

            profile = load_single_profile(yaml_file)
            assert profile["project_name"] is None
            assert profile["custom_input_path"] == "/custom/input/path"
            assert profile["custom_output_path"] == "/custom/output/path"

    def test_profile_with_all_options(self):
        """Test loading profile with project name and custom paths."""
        with TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "test_profile.yaml"
            yaml_file.write_text("""
project:
  name: "My Project"

paths:
  input: /input/dir
  output: /output/dir

Model:
  endpoint: test/model
  code-nickname: test

pricing:
  cost_per_frame: 0.01

duration_type: frames
fps: 24
duration_min: 1
duration_max: 100
duration_param_name: num_frames

params:
  resolution: "720p"
""")

            profile = load_single_profile(yaml_file)
            assert profile["project_name"] == "My Project"
            assert profile["custom_input_path"] == "/input/dir"
            assert profile["custom_output_path"] == "/output/dir"

    def test_profile_without_custom_options(self):
        """Test loading profile without custom options (backward compatibility)."""
        with TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "test_profile.yaml"
            yaml_file.write_text("""
Model:
  endpoint: test/model
  code-nickname: test

pricing:
  cost_per_frame: 0.01

duration_type: frames
fps: 24
duration_min: 1
duration_max: 100
duration_param_name: num_frames

params:
  resolution: "720p"
""")

            profile = load_single_profile(yaml_file)
            assert profile["project_name"] is None
            assert profile["custom_input_path"] is None
            assert profile["custom_output_path"] is None

    def test_project_name_as_string(self):
        """Test that project name can be specified as simple string."""
        with TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "test_profile.yaml"
            yaml_file.write_text("""
project: "Simple String Project"

Model:
  endpoint: test/model
  code-nickname: test

pricing:
  cost_per_frame: 0.01

duration_type: frames
fps: 24
duration_min: 1
duration_max: 100
duration_param_name: num_frames

params:
  resolution: "720p"
""")

            profile = load_single_profile(yaml_file)
            assert profile["project_name"] == "Simple String Project"


class TestInputDiscoveryWithCustomPath:
    """Tests for input discovery with custom paths."""

    def test_discover_with_custom_path(self):
        """Test that input discovery uses custom path when provided."""
        from src.processing.input_discovery import discover_markdown_jobs

        with TemporaryDirectory() as tmpdir:
            # Create a markdown file in the custom directory
            custom_dir = Path(tmpdir) / "custom_input"
            custom_dir.mkdir()
            (custom_dir / "test.md").write_text(
                "prompt\n10\n![img](http://example.com/image.jpg)"
            )

            # Discover should use the custom path
            files = discover_markdown_jobs(Path("/default/input"), str(custom_dir))
            assert len(files) == 1
            assert files[0].name == "test.md"

    def test_discover_without_custom_path(self):
        """Test that input discovery uses default path when not provided."""
        from src.processing.input_discovery import discover_markdown_jobs

        with TemporaryDirectory() as tmpdir:
            default_dir = Path(tmpdir)
            (default_dir / "test.md").write_text(
                "prompt\n10\n![img](http://example.com/image.jpg)"
            )

            # Discover should use the default path
            files = discover_markdown_jobs(default_dir, None)
            assert len(files) == 1
            assert files[0].name == "test.md"
