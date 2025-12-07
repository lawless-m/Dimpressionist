"""
Image utility functions for Dimpressionist.
"""

import io
from pathlib import Path
from typing import Tuple, Optional, List, Union
from PIL import Image


def create_thumbnail(
    image_path: Union[str, Path],
    size: int = 120,
    output_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Create a square thumbnail from an image.

    Args:
        image_path: Path to the source image
        size: Thumbnail size (square)
        output_path: Optional output path. If not provided, creates in same
                    directory with _thumb suffix

    Returns:
        Path to the created thumbnail
    """
    image_path = Path(image_path)

    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_thumb.jpg"
    else:
        output_path = Path(output_path)

    with Image.open(image_path) as img:
        # Convert to RGB if necessary (for PNG with alpha)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Create square crop from center
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim

        img_cropped = img.crop((left, top, right, bottom))
        img_thumb = img_cropped.resize((size, size), Image.Resampling.LANCZOS)
        img_thumb.save(output_path, "JPEG", quality=85)

    return output_path


def validate_image_dimensions(
    width: int,
    height: int,
    min_size: int = 256,
    max_size: int = 2048,
    multiple_of: int = 8
) -> Tuple[bool, Optional[str]]:
    """
    Validate image dimensions for generation.

    Args:
        width: Image width
        height: Image height
        min_size: Minimum allowed dimension
        max_size: Maximum allowed dimension
        multiple_of: Dimensions must be multiples of this value

    Returns:
        Tuple of (is_valid, error_message)
    """
    if width < min_size or height < min_size:
        return False, f"Dimensions must be at least {min_size}x{min_size}"

    if width > max_size or height > max_size:
        return False, f"Dimensions must not exceed {max_size}x{max_size}"

    if width % multiple_of != 0 or height % multiple_of != 0:
        return False, f"Dimensions must be multiples of {multiple_of}"

    return True, None


def normalize_dimensions(
    width: int,
    height: int,
    multiple_of: int = 8
) -> Tuple[int, int]:
    """
    Normalize dimensions to be multiples of a given value.

    Args:
        width: Original width
        height: Original height
        multiple_of: Dimensions will be rounded to nearest multiple

    Returns:
        Tuple of (normalized_width, normalized_height)
    """
    norm_width = round(width / multiple_of) * multiple_of
    norm_height = round(height / multiple_of) * multiple_of
    return norm_width, norm_height


def optimize_image_for_web(
    image_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    max_size: int = 1920,
    quality: int = 85
) -> Path:
    """
    Optimize an image for web display.

    Args:
        image_path: Path to source image
        output_path: Optional output path
        max_size: Maximum dimension (width or height)
        quality: JPEG quality (1-100)

    Returns:
        Path to optimized image
    """
    image_path = Path(image_path)

    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_web.jpg"
    else:
        output_path = Path(output_path)

    with Image.open(image_path) as img:
        # Convert to RGB
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if larger than max_size
        width, height = img.size
        if width > max_size or height > max_size:
            ratio = max_size / max(width, height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        img.save(output_path, "JPEG", quality=quality, optimize=True)

    return output_path


def image_to_bytes(
    image: Image.Image,
    format: str = "PNG",
    quality: int = 95
) -> bytes:
    """
    Convert PIL Image to bytes.

    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
        quality: Quality for JPEG

    Returns:
        Image as bytes
    """
    buffer = io.BytesIO()
    if format.upper() == "JPEG" and image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    image.save(buffer, format=format, quality=quality)
    buffer.seek(0)
    return buffer.getvalue()


def bytes_to_image(data: bytes) -> Image.Image:
    """
    Convert bytes to PIL Image.

    Args:
        data: Image bytes

    Returns:
        PIL Image object
    """
    return Image.open(io.BytesIO(data))


def get_image_info(image_path: Union[str, Path]) -> dict:
    """
    Get information about an image file.

    Args:
        image_path: Path to image

    Returns:
        Dictionary with image info
    """
    image_path = Path(image_path)

    with Image.open(image_path) as img:
        return {
            "path": str(image_path),
            "filename": image_path.name,
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "size_bytes": image_path.stat().st_size
        }


def batch_create_thumbnails(
    image_paths: List[Union[str, Path]],
    output_dir: Union[str, Path],
    size: int = 120
) -> List[Path]:
    """
    Create thumbnails for multiple images.

    Args:
        image_paths: List of source image paths
        output_dir: Directory to save thumbnails
        size: Thumbnail size

    Returns:
        List of paths to created thumbnails
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    thumbnails = []
    for image_path in image_paths:
        image_path = Path(image_path)
        thumb_path = output_dir / f"{image_path.stem}_thumb.jpg"
        try:
            create_thumbnail(image_path, size, thumb_path)
            thumbnails.append(thumb_path)
        except Exception as e:
            print(f"Warning: Could not create thumbnail for {image_path}: {e}")

    return thumbnails


def resize_for_img2img(
    image: Image.Image,
    target_width: int = 1024,
    target_height: int = 1024
) -> Image.Image:
    """
    Resize an image for img2img processing.

    Args:
        image: PIL Image to resize
        target_width: Target width
        target_height: Target height

    Returns:
        Resized PIL Image
    """
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
