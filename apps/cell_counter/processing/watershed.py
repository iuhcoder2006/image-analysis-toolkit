from __future__ import annotations

from dataclasses import dataclass
import time

import cv2
import numpy as np

from apps.cell_counter.processing.distance_transform import compute_distance_transform
from apps.cell_counter.processing.morphology import clean_binary_mask
from apps.cell_counter.processing.object_counter import analyze_markers
from apps.cell_counter.processing.preprocessing import gaussian_blur, to_grayscale
from apps.cell_counter.processing.threshold import apply_threshold
from shared.validators import validate_image_array


@dataclass(slots=True)
class CellCounterParams:
    gaussian_kernel: int = 5
    gaussian_sigma: float = 1.0
    threshold_method: str = "Otsu"
    manual_threshold: int = 127
    morphology_kernel: int = 3
    opening_iterations: int = 2
    dilation_iterations: int = 2
    distance_type: str = "L2"
    mask_size: int = 5
    distance_threshold_ratio: float = 0.4
    min_object_area: int = 50


@dataclass(slots=True)
class CellCounterResult:
    original: np.ndarray
    grayscale: np.ndarray
    blurred: np.ndarray
    binary: np.ndarray
    morphology: np.ndarray
    distance_map: np.ndarray
    normalized_distance_map: np.ndarray
    sure_foreground: np.ndarray
    sure_background: np.ndarray
    unknown_region: np.ndarray
    markers_before: np.ndarray
    markers_after: np.ndarray
    filtered_markers: np.ndarray
    marker_visualization: np.ndarray
    overlay: np.ndarray
    object_count: int
    object_areas: list[float]
    total_area: float
    average_area: float
    min_area: float
    max_area: float
    processing_time_ms: float
    threshold_value: float
    max_distance: float
    parameters: CellCounterParams


def run_watershed_pipeline(image: np.ndarray, params: CellCounterParams) -> CellCounterResult:
    validate_image_array(image)
    start = time.perf_counter()

    original = image.copy()
    color_image = original if original.ndim == 3 else cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)

    grayscale = to_grayscale(original)
    blurred = gaussian_blur(grayscale, params.gaussian_kernel, params.gaussian_sigma)
    binary, threshold_value = apply_threshold(blurred, params.threshold_method, params.manual_threshold)
    morphology, sure_background = clean_binary_mask(
        binary,
        params.morphology_kernel,
        params.opening_iterations,
        params.dilation_iterations,
    )

    distance_result = compute_distance_transform(
        morphology,
        params.distance_type,
        params.mask_size,
        params.distance_threshold_ratio,
    )

    sure_foreground = distance_result.sure_foreground
    sure_foreground_u8 = sure_foreground.astype(np.uint8)
    unknown_region = cv2.subtract(sure_background, sure_foreground_u8)
    _, markers_before = cv2.connectedComponents(sure_foreground_u8)
    watershed_markers = markers_before + 1
    watershed_markers[unknown_region == 255] = 0
    markers_after = cv2.watershed(color_image.copy(), watershed_markers.astype(np.int32))

    count_result = analyze_markers(color_image, markers_after, params.min_object_area)
    elapsed = (time.perf_counter() - start) * 1000

    return CellCounterResult(
        original=color_image,
        grayscale=grayscale,
        blurred=blurred,
        binary=binary,
        morphology=morphology,
        distance_map=distance_result.distance_map,
        normalized_distance_map=distance_result.normalized_map,
        sure_foreground=sure_foreground_u8,
        sure_background=sure_background,
        unknown_region=unknown_region,
        markers_before=markers_before,
        markers_after=markers_after,
        filtered_markers=count_result.filtered_markers,
        marker_visualization=count_result.marker_visualization,
        overlay=count_result.overlay,
        object_count=len(count_result.object_ids),
        object_areas=count_result.object_areas,
        total_area=count_result.total_area,
        average_area=count_result.average_area,
        min_area=count_result.min_area,
        max_area=count_result.max_area,
        processing_time_ms=elapsed,
        threshold_value=threshold_value,
        max_distance=distance_result.max_distance,
        parameters=params,
    )

