from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class FileToolbar(QWidget):
    openImageRequested = Signal()
    openVideoRequested = Signal()
    saveRequested = Signal()
    resetRequested = Signal()

    def __init__(self, include_video: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.open_image_button = QPushButton("Open Image")
        self.open_video_button = QPushButton("Open Video")
        self.save_button = QPushButton("Save Result")
        self.reset_button = QPushButton("Reset")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.open_image_button)
        if include_video:
            layout.addWidget(self.open_video_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.reset_button)
        layout.addStretch(1)

        self.open_image_button.clicked.connect(self.openImageRequested.emit)
        self.open_video_button.clicked.connect(self.openVideoRequested.emit)
        self.save_button.clicked.connect(self.saveRequested.emit)
        self.reset_button.clicked.connect(self.resetRequested.emit)

