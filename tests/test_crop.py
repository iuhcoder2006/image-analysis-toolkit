import numpy as np

from apps.image_viewer.processing.crop import apply_crop


def test_crop_returns_expected_shape() -> None:
    image = np.zeros((12, 14, 3), dtype=np.uint8)
    result = apply_crop(image, 2, 3, 5, 4)
    assert result.image.shape == (4, 5, 3)
    assert result.retained_percentage > 0

