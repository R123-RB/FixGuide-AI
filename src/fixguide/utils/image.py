"""Image preprocessing utilities."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image


def decode_base64_image(data: str) -> Image.Image:
    """Decode base64 string to PIL Image."""
    if data.startswith("data:image"):
        data = data.split(",")[1]
    return Image.open(BytesIO(base64.b64decode(data)))


def encode_image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Encode PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode()


def resize_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """Resize image maintaining aspect ratio."""
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return image


def validate_image(data: str) -> bool:
    """Validate base64 image data."""
    try:
        decode_base64_image(data)
        return True
    except Exception:
        return False


def capture_test_images(output_dir: str = "data/eval/images") -> Path:
    """Generate synthetic test images for vision evaluation.

    Creates placeholder images representing correct/incorrect repair states.
    Replace with real captured images for production evaluation.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Generate synthetic test images (colored rectangles as placeholders)
    states = [
        ("correct_state", (100, 200, 100)),  # Green = correct
        ("incorrect_state", (200, 100, 100)),  # Red = incorrect
    ]

    for name, color in states:
        img = Image.new("RGB", (640, 480), color)
        path = out / f"{name}.jpg"
        img.save(path, quality=85)

    return out
