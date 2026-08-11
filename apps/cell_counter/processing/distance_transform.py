from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


DISTANCE_TYPE_MAP = {
    "L1": cv2.DIST_L1,
    "L2": cv2.DIST_L2,
    "Chessboard": cv2.DIST_C,
}


@dataclass(slots=True)
class DistanceTransformResult:
    distance_map: np.ndarray
    normalized_map: np.ndarray
    sure_foreground: np.ndarray
    threshold_value: float
    max_distance: float


def compute_distance_transform(
    binary: np.ndarray,
    distance_type: str,
    mask_size: int,
    threshold_ratio: float,
) -> DistanceTransformResult:
    if distance_type not in DISTANCE_TYPE_MAP:
        raise ValueError(f"Unsupported distance type: {distance_type}")
    if mask_size not in {3, 5}:
        raise ValueError("Mask size must be 3 or 5.")
    if not 0 < threshold_ratio < 1:
        raise ValueError("Distance threshold ratio must be between 0 and 1.")

    distance_map = cv2.distanceTransform(binary, DISTANCE_TYPE_MAP[distance_type], mask_size)
    normalized = cv2.normalize(distance_map, None, 0, 255, cv2.NORM_MINMAX)
    max_distance = float(distance_map.max()) if distance_map.size else 0.0
    threshold_value = threshold_ratio * max_distance
    _, sure_foreground = cv2.threshold(distance_map, threshold_value, 255, cv2.THRESH_BINARY)

    return DistanceTransformResult(
        distance_map=distance_map,
        normalized_map=normalized.astype(np.uint8),
        sure_foreground=sure_foreground.astype(np.uint8),
        threshold_value=threshold_value,
        max_distance=max_distance,
    )

