from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget


class SegmentedControl(QWidget):
    """A compact, QSS-friendly replacement for a default QTabWidget header."""

    currentTextChanged = Signal(str)

    def __init__(self, labels: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: list[QPushButton] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        for index, label in enumerate(labels):
            button = QPushButton(label)
            button.setObjectName("segmentButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            self._group.addButton(button, index)
            self._buttons.append(button)
            layout.addWidget(button)
        self._group.buttonClicked.connect(lambda button: self.currentTextChanged.emit(button.text()))

    def current_text(self) -> str:
        button = self._group.checkedButton()
        return button.text() if button else ""

    def set_current_text(self, text: str) -> None:
        for button in self._buttons:
            if button.text() == text:
                button.setChecked(True)
                self.currentTextChanged.emit(text)
                return
