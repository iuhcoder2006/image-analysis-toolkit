import numpy as np

from apps.image_viewer.processing.zoom import apply_zoom


def test_zoom_output_dimensions_are_correct() -> None:
    image = np.zeros((20, 10, 3), dtype=np.uint8)
    result = apply_zoom(image, 2.0, "Nearest Neighbor")
    assert result.output_size == (20, 40)
    assert result.image.shape[:2] == (40, 20)

