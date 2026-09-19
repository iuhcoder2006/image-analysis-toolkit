from __future__ import annotations

import time

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from apps.cell_counter.processing.distance_transform import compute_distance_transform
from apps.cell_counter.processing.morphology import clean_binary_mask
from apps.cell_counter.processing.object_counter import analyze_markers
from apps.cell_counter.processing.preprocessing import gaussian_blur, to_grayscale
from apps.cell_counter.processing.threshold import apply_threshold
from apps.cell_counter.processing.watershed import CellCounterParams, CellCounterResult


class ProgressiveSegmentationWorker(QObject):
    """Runs the existing watershed primitives and emits each stage only after it exists."""

    stage_ready = Signal(str, object)
    finished = Signal(object)
    failed = Signal(str)

    @Slot(object, object)
    def run(self, image: np.ndarray, params: CellCounterParams) -> None:
        try:
            started = time.perf_counter()
            original = image.copy()
            color_image = original if original.ndim == 3 else cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
            self.stage_ready.emit("Original", color_image)

            grayscale = to_grayscale(original)
            self.stage_ready.emit("Grayscale", grayscale)
            blurred = gaussian_blur(grayscale, params.gaussian_kernel, params.gaussian_sigma)
            binary, threshold_value = apply_threshold(blurred, params.threshold_method, params.manual_threshold)
            self.stage_ready.emit("Threshold", binary)
            morphology, sure_background = clean_binary_mask(
                binary, params.morphology_kernel, params.opening_iterations, params.dilation_iterations
            )
            self.stage_ready.emit("Morphology", morphology)
            distance_result = compute_distance_transform(
                morphology, params.distance_type, params.mask_size, params.distance_threshold_ratio
            )
            self.stage_ready.emit("Distance Transform", distance_result.normalized_map)
            sure_foreground = distance_result.sure_foreground.astype(np.uint8)
            unknown_region = cv2.subtract(sure_background, sure_foreground)
            _, markers_before = cv2.connectedComponents(sure_foreground)
            self.stage_ready.emit("Markers", markers_before)
            watershed_markers = markers_before + 1
            watershed_markers[unknown_region == 255] = 0
            markers_after = cv2.watershed(color_image.copy(), watershed_markers.astype(np.int32))
            count_result = analyze_markers(color_image, markers_after, params.min_object_area)
            self.stage_ready.emit("Watershed", count_result.marker_visualization)
            elapsed = (time.perf_counter() - started) * 1000
            result = CellCounterResult(
                original=color_image,
                grayscale=grayscale,
                blurred=blurred,
                binary=binary,
                morphology=morphology,
                distance_map=distance_result.distance_map,
                normalized_distance_map=distance_result.normalized_map,
                sure_foreground=sure_foreground,
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
            self.stage_ready.emit("Final Overlay", result.overlay)
            self.finished.emit(result)
        except Exception as error:  # pragma: no cover - user data / GUI pathway
            self.failed.emit(str(error))
