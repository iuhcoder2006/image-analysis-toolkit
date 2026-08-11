from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from shared.constants import IMAGE_EXTENSIONS


def list_images(folder: str | Path) -> list[Path]:
    path = Path(folder)
    if not path.exists():
        return []
    return sorted(item for item in path.iterdir() if item.suffix.lower() in IMAGE_EXTENSIONS)


def load_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to load image: {path}")
    return image


def save_image(path: str | Path, image: np.ndarray) -> None:
    success = cv2.imwrite(str(path), image)
    if not success:
        raise ValueError(f"Unable to save image: {path}")

