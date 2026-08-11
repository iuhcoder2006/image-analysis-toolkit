from __future__ import annotations

import numpy as np
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from shared.image_utils import numpy_to_qpixmap


class PipelineVisualizer(QWidget):
    stageSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setIconSize(QSize(96, 72))
        self.list_widget.setSpacing(12)
        self.list_widget.currentItemChanged.connect(self._on_item_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list_widget)

    def set_stages(self, stages: dict[str, np.ndarray]) -> None:
        self.list_widget.clear()
        for name, image in stages.items():
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setIcon(QIcon(numpy_to_qpixmap(image)))
            self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def select_stage(self, name: str) -> None:
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self.list_widget.setCurrentItem(item)
                return

    def _on_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is not None:
            self.stageSelected.emit(current.data(Qt.ItemDataRole.UserRole))
