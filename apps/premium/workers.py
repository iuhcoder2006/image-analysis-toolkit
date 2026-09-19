from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from apps.image_viewer.processing.crop import apply_crop
from apps.image_viewer.processing.rotate import apply_rotation
from apps.image_viewer.processing.zoom import apply_zoom


@dataclass(frozen=True, slots=True)
class TransformRequest:
    generation: int
    operation: str
    image: np.ndarray
    parameters: dict


class TransformWorker(QObject):
    finished = Signal(int, object)
    failed = Signal(int, str)

    @Slot(object)
    def run(self, request: TransformRequest) -> None:
        try:
            if request.operation == "Zoom":
                result = apply_zoom(request.image, request.parameters["scale"], request.parameters["interpolation"])
            elif request.operation == "Rotate":
                result = apply_rotation(
                    request.image,
                    request.parameters["angle"],
                    request.parameters["interpolation"],
                    request.parameters["border_mode"],
                )
            else:
                result = apply_crop(
                    request.image,
                    request.parameters["x"],
                    request.parameters["y"],
                    request.parameters["width"],
                    request.parameters["height"],
                )
            self.finished.emit(request.generation, result)
        except Exception as error:  # pragma: no cover - user data / GUI path
            self.failed.emit(request.generation, str(error))

