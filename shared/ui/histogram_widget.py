from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class HistogramWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(4, 2.5), facecolor="#1b1e24")
        self.canvas = FigureCanvasQTAgg(self.figure)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def plot_images(self, original: np.ndarray | None, result: np.ndarray | None) -> None:
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        axis.set_facecolor("#1b1e24")
        axis.tick_params(colors="#d5d9e2")
        axis.spines["bottom"].set_color("#485064")
        axis.spines["left"].set_color("#485064")
        axis.set_title("Histogram Comparison", color="#f1f3f8")

        if original is not None:
            axis.hist(original.ravel(), bins=32, alpha=0.45, color="#5b8cff", label="Original")
        if result is not None:
            axis.hist(result.ravel(), bins=32, alpha=0.45, color="#4cc38a", label="Result")

        if original is not None or result is not None:
            axis.legend(facecolor="#1b1e24", edgecolor="#485064", labelcolor="#f1f3f8")

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def plot_values(self, values: list[float], title: str = "Distribution", bins: int = 12) -> None:
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        axis.set_facecolor("#1b1e24")
        axis.tick_params(colors="#d5d9e2")
        axis.spines["bottom"].set_color("#485064")
        axis.spines["left"].set_color("#485064")
        axis.set_title(title, color="#f1f3f8")
        if values:
            axis.hist(values, bins=bins, color="#5b8cff", edgecolor="#0f1115")
        self.figure.tight_layout()
        self.canvas.draw_idle()

