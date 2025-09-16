"""Tests for duration handling functionality."""
import pytest
from src.processing.duration_handler import (
    process_duration,
    _process_frame_duration,
    _process_seconds_duration,
    get_duration_parameter_name,
    should_include_fps
)


class TestFrameDuration:
    """Test frame-based duration processing."""
    
    def test_frame_duration_within_bounds(self):
        """Test frames within min/max bounds."""
        frames, adjusted, info = _process_frame_duration(50, 10, 100)
        assert frames == 50
        assert not adjusted
        assert info['original'] == 50
        assert info['adjusted'] == 50
        assert info['reason'] is None
    
    def test_frame_duration_below_minimum(self):
        """Test frames below minimum."""
        frames, adjusted, info = _process_frame_duration(5, 10, 100)
        assert frames == 10
        assert adjusted
        assert info['original'] == 5
        assert info['adjusted'] == 10
        assert "Below minimum" in info['reason']
    
    def test_frame_duration_above_maximum(self):
        """Test frames above maximum."""
        frames, adjusted, info = _process_frame_duration(150, 10, 100)
        assert frames == 100
        assert adjusted
        assert info['original'] == 150
        assert info['adjusted'] == 100
        assert "Exceeded maximum" in info['reason']


class TestSecondsDuration:
    """Test seconds-based duration processing."""
    
    def test_seconds_duration_within_bounds(self):
        """Test seconds within min/max bounds."""
        seconds, adjusted, info = _process_seconds_duration(150, 30, 3, 10)
        # 150 frames / 30 fps = 5 seconds (within 3-10 range)
        assert seconds == 5
        assert not adjusted
        assert info['original_frames'] == 150
        assert info['original_seconds'] == 5
        assert info['adjusted_seconds'] == 5
        assert info['reason'] is None
    
    def test_seconds_duration_below_minimum(self):
        """Test seconds below minimum."""
        seconds, adjusted, info = _process_seconds_duration(50, 30, 3, 10)
        # 50 frames / 30 fps = 1.67, rounds up to 2 seconds (below 3)
        assert seconds == 3
        assert adjusted
        assert info['original_frames'] == 50
        assert info['original_seconds'] == 2
        assert info['adjusted_seconds'] == 3
        assert "Below minimum" in info['reason']
    
    def test_seconds_duration_above_maximum(self):
        """Test seconds above maximum."""
        seconds, adjusted, info = _process_seconds_duration(400, 30, 3, 10)
        # 400 frames / 30 fps = 13.33, rounds up to 14 seconds (above 10)
        assert seconds == 10
        assert adjusted
        assert info['original_frames'] == 400
        assert info['original_seconds'] == 14
        assert info['adjusted_seconds'] == 10
        assert "Exceeded maximum" in info['reason']
    
    def test_seconds_rounding_up(self):
        """Test that seconds always round up."""
        seconds, _, info = _process_seconds_duration(100, 30, 1, 10)
        # 100 frames / 30 fps = 3.33, should round up to 4
        assert info['original_seconds'] == 4


class TestProcessDuration:
    """Test main duration processing function."""
    
    def test_process_duration_frames(self):
        """Test processing with frame-based profile."""
        profile = {
            'duration_config': {
                'duration_type': 'frames',
                'fps': 24,
                'duration_min': 30,
                'duration_max': 100,
                'duration_param_name': 'num_frames'
            }
        }
        value, adjusted, info = process_duration(50, profile)
        assert value == 50
        assert not adjusted
        assert info['type'] == 'frames'
    
    def test_process_duration_seconds(self):
        """Test processing with seconds-based profile."""
        profile = {
            'duration_config': {
                'duration_type': 'seconds',
                'fps': 25,
                'duration_min': 3,
                'duration_max': 10,
                'duration_param_name': 'duration'
            }
        }
        value, adjusted, info = process_duration(125, profile)
        # 125 frames / 25 fps = 5 seconds
        assert value == 5
        assert not adjusted
        assert info['type'] == 'seconds'
    
    def test_invalid_duration_type(self):
        """Test with invalid duration type."""
        profile = {
            'duration_config': {
                'duration_type': 'invalid',
                'fps': 24,
                'duration_min': 30,
                'duration_max': 100,
                'duration_param_name': 'duration'
            }
        }
        with pytest.raises(ValueError, match="Invalid duration_type"):
            process_duration(50, profile)


class TestParameterHelpers:
    """Test helper functions for parameter handling."""
    
    def test_get_duration_parameter_name(self):
        """Test getting parameter name from profile."""
        profile = {
            'duration_config': {
                'duration_param_name': 'custom_duration'
            }
        }
        assert get_duration_parameter_name(profile) == 'custom_duration'
    
    def test_should_include_fps_true(self):
        """Test FPS inclusion when present in parameters."""
        profile = {
            'parameters': {
                'fps': 24,
                'resolution': '1080p'
            }
        }
        assert should_include_fps(profile) is True
    
    def test_should_include_fps_false(self):
        """Test FPS not included when absent from parameters."""
        profile = {
            'parameters': {
                'resolution': '1080p'
            }
        }
        assert should_include_fps(profile) is False
    
    def test_should_include_fps_no_params(self):
        """Test FPS handling with no parameters section."""
        profile = {}
        assert should_include_fps(profile) is False