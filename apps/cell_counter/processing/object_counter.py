from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(slots=True)
class ObjectCountResult:
    filtered_markers: np.ndarray
    marker_visualization: np.ndarray
    overlay: np.ndarray
    object_ids: list[int]
    object_areas: list[float]
    total_area: float
    average_area: float
    min_area: float
    max_area: float


def create_marker_visualization(markers: np.ndarray) -> np.ndarray:
    shifted = markers.copy().astype(np.float32)
    shifted[shifted < 0] = 0
    normalized = cv2.normalize(shifted, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return cv2.applyColorMap(normalized, cv2.COLORMAP_TURBO)


def filter_object_ids(markers: np.ndarray, min_object_area: int) -> tuple[np.ndarray, list[int], list[float]]:
    filtered = markers.copy()
    object_ids: list[int] = []
    object_areas: list[float] = []

    for marker_id in sorted(int(value) for value in np.unique(markers) if value > 1):
        area = float(np.count_nonzero(markers == marker_id))
        if area >= min_object_area:
            object_ids.append(marker_id)
            object_areas.append(area)
        else:
            filtered[filtered == marker_id] = 0

    return filtered, object_ids, object_areas


def compose_overlay(
    original: np.ndarray,
    filtered_markers: np.ndarray,
    object_ids: list[int],
    show_boundaries: bool = True,
    show_labels: bool = True,
    show_markers: bool = False,
    marker_visualization: np.ndarray | None = None,
) -> np.ndarray:
    overlay = original.copy()
    if overlay.ndim == 2:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)

    if show_markers and marker_visualization is not None:
        overlay = cv2.addWeighted(overlay, 0.55, marker_visualization, 0.45, 0)

    if show_boundaries:
        overlay[filtered_markers == -1] = (0, 0, 255)

    if show_labels:
        for marker_id in object_ids:
            ys, xs = np.where(filtered_markers == marker_id)
            if xs.size == 0 or ys.size == 0:
                continue
            center = (int(xs.mean()), int(ys.mean()))
            cv2.putText(
                overlay,
                str(marker_id - 1),
                center,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    return overlay


def analyze_markers(original: np.ndarray, markers: np.ndarray, min_object_area: int) -> ObjectCountResult:
    filtered_markers, object_ids, object_areas = filter_object_ids(markers, min_object_area)
    marker_visualization = create_marker_visualization(filtered_markers)
    overlay = compose_overlay(original, filtered_markers, object_ids, True, True, False, marker_visualization)

    total_area = float(sum(object_areas))
    average_area = total_area / len(object_areas) if object_areas else 0.0

    return ObjectCountResult(
        filtered_markers=filtered_markers,
        marker_visualization=marker_visualization,
        overlay=overlay,
        object_ids=object_ids,
        object_areas=object_areas,
        total_area=total_area,
        average_area=average_area,
        min_area=min(object_areas) if object_areas else 0.0,
        max_area=max(object_areas) if object_areas else 0.0,
    )

