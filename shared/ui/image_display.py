from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from shared.image_utils import numpy_to_qpixmap, scale_pixmap_for_viewport


class ImageDisplay(QWidget):
    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image: np.ndarray | None = None
        self._pixmap = None
        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelTitle")
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(240, 200)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setObjectName("imageViewport")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label, 1)

    @property
    def image(self) -> np.ndarray | None:
        return self._image

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_image(self, image: np.ndarray | None) -> None:
        self._image = image
        if image is None:
            self._pixmap = None
            self.image_label.setText("No image loaded")
            self.image_label.clear()
            return

        self._pixmap = numpy_to_qpixmap(image)
        self._refresh_pixmap()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_pixmap()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._pixmap is None:
            return
        scaled = scale_pixmap_for_viewport(
            self._pixmap,
            self.image_label.size(),
            self.image_label.devicePixelRatioF(),
        )
        self.image_label.setPixmap(scaled)

