from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QWidget

from shared.ui.image_display import ImageDisplay


class BeforeAfterView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.original_display = ImageDisplay("Original")
        self.result_display = ImageDisplay("Result")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.original_display, 1)
        layout.addWidget(self.result_display, 1)

