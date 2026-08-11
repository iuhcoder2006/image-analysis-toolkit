from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_first_video_frame(path: str | Path) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {path}")

    success, frame = capture.read()
    capture.release()

    if not success or frame is None:
        raise ValueError(f"Unable to read first frame: {path}")
    return frame

