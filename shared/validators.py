from __future__ import annotations

from typing import Iterable

import numpy as np


def validate_image_array(image: np.ndarray | None) -> None:
    if image is None:
        raise ValueError("No image is loaded.")
    if not isinstance(image, np.ndarray):
        raise TypeError("Image must be a NumPy array.")
    if image.size == 0:
        raise ValueError("Image is empty.")


def validate_crop_rect(x: int, y: int, width: int, height: int, image_shape: Iterable[int]) -> None:
    if width <= 0 or height <= 0:
        raise ValueError("Crop width and height must be positive.")

    shape = tuple(image_shape)
    max_height, max_width = shape[:2]

    if x < 0 or y < 0:
        raise ValueError("Crop coordinates must be non-negative.")
    if x + width > max_width or y + height > max_height:
        raise ValueError("Crop rectangle is outside the image bounds.")

