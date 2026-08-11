import numpy as np

from apps.cell_counter.processing.distance_transform import compute_distance_transform


def test_distance_transform_shape_matches_input() -> None:
    image = np.zeros((20, 20), dtype=np.uint8)
    image[5:15, 5:15] = 255
    result = compute_distance_transform(image, "L2", 5, 0.4)
    assert result.distance_map.shape == image.shape
    assert result.max_distance > 0

