from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class MetricCard(QFrame):
    def __init__(self, caption: str, value: str = "—", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setMinimumHeight(76)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("kpiValue")
        caption_label = QLabel(caption)
        caption_label.setObjectName("kpiCaption")
        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class InlineAlert(QFrame):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setVisible(False)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

    def show_message(self, text: str, color: str = "#F5A524") -> None:
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {color};")
        self.setVisible(True)

    def clear(self) -> None:
        self.setVisible(False)


class Filmstrip(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        add_button = QPushButton("＋")
        add_button.setToolTip("Open an image")
        add_button.setFixedSize(42, 42)
        self.filename = QLabel("No image selected")
        self.filename.setObjectName("sectionTitle")
        self.detail = QLabel("Open an image to start a transform workflow")
        self.detail.setObjectName("metadata")
        info = QVBoxLayout()
        info.setSpacing(0)
        info.addWidget(self.filename)
        info.addWidget(self.detail)
        layout.addWidget(add_button)
        layout.addLayout(info)
        layout.addStretch(1)
        self.open_requested = add_button.clicked

    def set_file(self, name: str, detail: str) -> None:
        self.filename.setText(name)
        self.detail.setText(detail)
