from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

from shared.validators import validate_crop_rect, validate_image_array


@dataclass(slots=True)
class CropResult:
    image: np.ndarray
    rect: tuple[int, int, int, int]
    original_area: int
    crop_area: int
    retained_percentage: float
    processing_time_ms: float


def apply_crop(image: np.ndarray, x: int, y: int, width: int, height: int) -> CropResult:
    validate_image_array(image)
    validate_crop_rect(x, y, width, height, image.shape)

    start = time.perf_counter()
    cropped = image[y : y + height, x : x + width].copy()
    elapsed = (time.perf_counter() - start) * 1000

    original_area = int(image.shape[0] * image.shape[1])
    crop_area = int(width * height)

    return CropResult(
        image=cropped,
        rect=(x, y, width, height),
        original_area=original_area,
        crop_area=crop_area,
        retained_percentage=(crop_area / original_area) * 100 if original_area else 0.0,
        processing_time_ms=elapsed,
    )

