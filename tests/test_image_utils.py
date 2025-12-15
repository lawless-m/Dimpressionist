"""
Unit tests for image utilities.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image

from src.utils.image_utils import (
    create_thumbnail,
    validate_image_dimensions,
    normalize_dimensions,
    optimize_image_for_web,
    image_to_bytes,
    bytes_to_image,
    get_image_info,
)


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    with TemporaryDirectory() as tmpdir:
        img = Image.new('RGB', (1024, 1024), color='red')
        path = Path(tmpdir) / "test_image.png"
        img.save(path)
        yield path


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestCreateThumbnail:
    """Tests for thumbnail creation."""

    def test_create_thumbnail(self, sample_image, temp_dir):
        """Test creating a thumbnail."""
        output = temp_dir / "thumb.jpg"
        result = create_thumbnail(sample_image, size=120, output_path=output)

        assert result.exists()
        with Image.open(result) as img:
            assert img.size == (120, 120)

    def test_auto_output_path(self, temp_dir):
        """Test automatic output path generation."""
        # Create image in temp dir
        img = Image.new('RGB', (500, 500), color='blue')
        source = temp_dir / "source.png"
        img.save(source)

        result = create_thumbnail(source, size=100)

        assert result.name == "source_thumb.jpg"
        assert result.exists()


class TestValidateDimensions:
    """Tests for dimension validation."""

    def test_valid_dimensions(self):
        """Test valid dimensions."""
        valid, error = validate_image_dimensions(1024, 1024)
        assert valid
        assert error is None

    def test_too_small(self):
        """Test dimensions too small."""
        valid, error = validate_image_dimensions(128, 128)
        assert not valid
        assert "at least" in error

    def test_too_large(self):
        """Test dimensions too large."""
        valid, error = validate_image_dimensions(4096, 4096)
        assert not valid
        assert "exceed" in error

    def test_not_multiple(self):
        """Test dimensions not multiple of 8."""
        valid, error = validate_image_dimensions(1000, 1000)
        assert not valid
        assert "multiples" in error


class TestNormalizeDimensions:
    """Tests for dimension normalization."""

    def test_normalize_to_multiple(self):
        """Test normalizing to nearest multiple."""
        w, h = normalize_dimensions(1000, 1000, multiple_of=8)
        assert w == 1000  # 1000 rounds to 1000 (125 * 8)
        assert h == 1000

    def test_already_normalized(self):
        """Test already normalized dimensions."""
        w, h = normalize_dimensions(1024, 768, multiple_of=8)
        assert w == 1024
        assert h == 768


class TestOptimizeForWeb:
    """Tests for web optimization."""

    def test_optimize(self, sample_image, temp_dir):
        """Test basic optimization."""
        output = temp_dir / "web.jpg"
        result = optimize_image_for_web(sample_image, output_path=output)

        assert result.exists()
        # Check it's a JPEG
        with Image.open(result) as img:
            assert img.format == "JPEG"

    def test_resize_large_image(self, temp_dir):
        """Test resizing large images."""
        # Create large image
        img = Image.new('RGB', (4000, 3000), color='green')
        source = temp_dir / "large.png"
        img.save(source)

        result = optimize_image_for_web(source, max_size=1920)

        with Image.open(result) as optimized:
            assert max(optimized.size) <= 1920


class TestImageConversion:
    """Tests for image byte conversion."""

    def test_to_bytes_and_back(self):
        """Test converting to bytes and back."""
        original = Image.new('RGB', (100, 100), color='purple')
        data = image_to_bytes(original, format="PNG")
        restored = bytes_to_image(data)

        assert restored.size == original.size
        assert restored.mode == original.mode


class TestGetImageInfo:
    """Tests for image info extraction."""

    def test_get_info(self, sample_image):
        """Test getting image information."""
        info = get_image_info(sample_image)

        assert info["width"] == 1024
        assert info["height"] == 1024
        assert info["format"] == "PNG"
        assert info["mode"] == "RGB"
        assert "size_bytes" in info
