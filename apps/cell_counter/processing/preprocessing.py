from __future__ import annotations

import cv2
import numpy as np

from shared.validators import validate_image_array


def to_grayscale(image: np.ndarray) -> np.ndarray:
    validate_image_array(image)
    if image.ndim == 2:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def gaussian_blur(image: np.ndarray, kernel_size: int, sigma: float) -> np.ndarray:
    if kernel_size <= 0 or kernel_size % 2 == 0:
        raise ValueError("Gaussian kernel size must be a positive odd number.")
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigmaX=sigma)

