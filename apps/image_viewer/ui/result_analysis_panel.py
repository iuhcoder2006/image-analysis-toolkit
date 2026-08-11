from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from shared.ui.histogram_widget import HistogramWidget


class ResultAnalysisPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.metric_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for key in [
            "Original Size",
            "Output Size",
            "Scale / Angle",
            "Interpolation",
            "Border / Clip",
            "Crop / Retained",
            "Time",
        ]:
            label = QLabel("-")
            label.setWordWrap(True)
            self.metric_labels[key] = label
            form.addRow(f"{key}:", label)

        self.histogram = HistogramWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(self.histogram, 1)

    def update_metrics(self, operation: str, metadata: dict | None, original: np.ndarray | None, result: np.ndarray | None) -> None:
        metadata = metadata or {}
        self.metric_labels["Original Size"].setText(self._format_size(metadata.get("original_size")))
        self.metric_labels["Output Size"].setText(self._format_size(metadata.get("output_size")))
        self.metric_labels["Interpolation"].setText(str(metadata.get("interpolation", "-")))
        self.metric_labels["Time"].setText(f'{metadata.get("processing_time_ms", 0.0):.2f} ms' if metadata else "-")

        if operation == "Zoom":
            self.metric_labels["Scale / Angle"].setText(f'{metadata.get("scale", 1.0):.2f}x')
            self.metric_labels["Border / Clip"].setText("Not applicable")
            self.metric_labels["Crop / Retained"].setText("Not applicable")
        elif operation == "Rotate":
            clipping = "Yes" if metadata.get("clipping_occurs") else "No"
            self.metric_labels["Scale / Angle"].setText(f'{metadata.get("angle", 0):.0f}°')
            self.metric_labels["Border / Clip"].setText(f'{metadata.get("border_mode", "-")} / Clipping: {clipping}')
            self.metric_labels["Crop / Retained"].setText("Not applicable")
        else:
            retained = metadata.get("retained_percentage")
            rect = metadata.get("rect", (0, 0, 0, 0))
            retained_text = f"{retained:.1f}%" if retained is not None else "-"
            self.metric_labels["Scale / Angle"].setText("Not applicable")
            self.metric_labels["Border / Clip"].setText("Not applicable")
            self.metric_labels["Crop / Retained"].setText(f"{rect} / {retained_text}")

        self.histogram.plot_images(original, result)

    @staticmethod
    def _format_size(size: tuple[int, int] | None) -> str:
        if not size:
            return "-"
        return f"{size[0]} x {size[1]}"

