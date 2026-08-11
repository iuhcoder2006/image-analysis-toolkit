import numpy as np

from apps.cell_counter.processing.object_counter import analyze_markers


def test_object_counter_counts_synthetic_labels() -> None:
    original = np.zeros((10, 10, 3), dtype=np.uint8)
    markers = np.zeros((10, 10), dtype=np.int32)
    markers[1:4, 1:4] = 2
    markers[5:8, 5:9] = 3
    markers[0, :] = -1

    result = analyze_markers(original, markers, min_object_area=4)
    assert len(result.object_ids) == 2
    assert result.total_area == sum(result.object_areas)
    assert result.overlay.shape == original.shape

