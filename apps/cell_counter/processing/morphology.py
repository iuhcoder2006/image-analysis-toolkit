from __future__ import annotations

import cv2
import numpy as np


def clean_binary_mask(
    binary: np.ndarray,
    kernel_size: int,
    opening_iterations: int,
    dilation_iterations: int,
) -> tuple[np.ndarray, np.ndarray]:
    if kernel_size <= 0:
        raise ValueError("Morphology kernel size must be positive.")
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=opening_iterations)
    sure_background = cv2.dilate(opened, kernel, iterations=dilation_iterations)
    return opened, sure_background

