"""Tests for domain models."""
from pathlib import Path
from src.models.generation import GenerationContext
from src.models.profile import VideoProfile
from src.models.triplet import InputTriplet


class TestGenerationContext:
    """Tests for GenerationContext model."""
    
    def test_creation(self):
        """Test creating a GenerationContext."""
        context = GenerationContext(
            prompt_file=Path("prompt.txt"),
            image_url_file=Path("image.txt"),
            num_frames_file=Path("frames.txt"),
            output_dir=Path("output"),
            prompt="test prompt",
            image_url="http://example.com/image.jpg",
            num_frames=100,
            profile={"name": "test"},
            params={"resolution": "480p"},
            video_url="http://example.com/video.mp4",
            video_path=Path("video.mp4"),
            cost=1.0
        )
        assert context.prompt == "test prompt"
        assert context.num_frames == 100
        assert context.cost == 1.0


class TestVideoProfile:
    """Tests for VideoProfile model."""
    
    def test_creation(self):
        """Test creating a VideoProfile."""
        profile = VideoProfile(
            name="test_profile",
            model_id="model/endpoint",
            nickname="test",
            pricing={"cost_per_frame": 0.001},
            parameters={"resolution": "480p"}
        )
        assert profile.name == "test_profile"
        assert profile.model_id == "model/endpoint"
    


class TestInputTriplet:
    """Tests for InputTriplet model."""
    
    def test_creation(self):
        """Test creating an InputTriplet."""
        triplet = InputTriplet(
            prompt_file=Path("prompt.txt"),
            image_url_file=Path("image.txt"),
            num_frames_file=Path("frames.txt")
        )
        assert triplet.prompt_file == Path("prompt.txt")
    
    def test_unpacking(self):
        """Test unpacking InputTriplet."""
        triplet = InputTriplet(
            prompt_file=Path("prompt.txt"),
            image_url_file=Path("image.txt"),
            num_frames_file=Path("frames.txt")
        )
        prompt, image, frames = triplet
        assert prompt == Path("prompt.txt")
        assert image == Path("image.txt")
        assert frames == Path("frames.txt")