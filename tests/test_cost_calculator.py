"""Tests for cost calculator."""
import pytest
from src.processing.cost_calculator import calculate_video_cost, _validate_numeric_field


class TestValidateNumericField:
    """Tests for _validate_numeric_field function."""
    
    def test_valid_integer(self):
        """Test with valid integer value."""
        _validate_numeric_field(10, "test_field", "test_profile")
    
    def test_valid_float(self):
        """Test with valid float value."""
        _validate_numeric_field(10.5, "test_field", "test_profile")
    
    def test_zero_value(self):
        """Test with zero value (valid)."""
        _validate_numeric_field(0, "test_field", "test_profile")
    
    def test_negative_value(self):
        """Test with negative value (invalid)."""
        with pytest.raises(ValueError, match="invalid test_field"):
            _validate_numeric_field(-1, "test_field", "test_profile")
    
    def test_non_numeric_value(self):
        """Test with non-numeric value (invalid)."""
        with pytest.raises(ValueError, match="invalid test_field"):
            _validate_numeric_field("not_a_number", "test_field", "test_profile")


class TestCalculateVideoCost:
    """Tests for calculate_video_cost function."""
    
    def test_frame_based_pricing(self):
        """Test frame-based pricing model."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_frame": 0.001}
        }
        cost = calculate_video_cost(profile, 100)
        assert cost == 0.1
    
    def test_prediction_based_pricing(self):
        """Test prediction-based pricing model."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_prediction": 5.0}
        }
        cost = calculate_video_cost(profile, 100)
        assert cost == 5.0
    
    def test_time_based_pricing(self):
        """Test time-based pricing model."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_second": 0.01}
        }
        # 100 frames * 3 seconds per frame = 300 seconds
        cost = calculate_video_cost(profile, 100)
        assert cost == 3.0
    
    def test_missing_pricing_section(self):
        """Test with missing pricing section."""
        profile = {"name": "test_profile"}
        with pytest.raises(ValueError, match="missing pricing configuration"):
            calculate_video_cost(profile, 100)
    
    def test_invalid_pricing_model(self):
        """Test with invalid pricing model."""
        profile = {
            "name": "test_profile",
            "pricing": {"invalid_field": 1.0}
        }
        with pytest.raises(ValueError, match="must have one of"):
            calculate_video_cost(profile, 100)