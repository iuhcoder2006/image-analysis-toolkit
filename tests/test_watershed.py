import cv2
import numpy as np

from apps.cell_counter.processing.watershed import CellCounterParams, run_watershed_pipeline


def test_watershed_returns_marker_map_with_correct_dimensions() -> None:
    image = np.zeros((120, 120, 3), dtype=np.uint8)
    cv2.circle(image, (40, 60), 20, (255, 255, 255), -1)
    cv2.circle(image, (80, 60), 20, (255, 255, 255), -1)

    result = run_watershed_pipeline(image, CellCounterParams(distance_threshold_ratio=0.3, min_object_area=20))
    assert result.markers_after.shape == image.shape[:2]
    assert result.object_count >= 1

