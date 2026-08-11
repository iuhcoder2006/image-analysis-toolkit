from __future__ import annotations

import cv2
import numpy as np


def apply_threshold(image: np.ndarray, method: str, threshold_value: int = 127) -> tuple[np.ndarray, float]:
    if method == "Otsu":
        used_threshold, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "Binary":
        used_threshold, binary = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)
    elif method == "Adaptive":
        used_threshold = -1.0
        binary = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            21,
            5,
        )
    else:
        raise ValueError(f"Unsupported threshold method: {method}")

    white_ratio = float(np.count_nonzero(binary)) / float(binary.size)
    if white_ratio > 0.55:
        binary = cv2.bitwise_not(binary)

    return binary, float(used_threshold)

