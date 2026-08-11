from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.cell_counter.processing.watershed import CellCounterParams, CellCounterResult
from shared.ui.histogram_widget import HistogramWidget


class ResultAnalysisPanel(QWidget):
    displayOptionsChanged = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.metric_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for key in [
            "Objects Detected",
            "Total Area (px)",
            "Average Area (px)",
            "Min Area (px)",
            "Max Area (px)",
            "Processing Time",
            "Parameters",
        ]:
            label = QLabel("-")
            label.setWordWrap(True)
            self.metric_labels[key] = label
            form.addRow(f"{key}:", label)

        visualization_box = QGroupBox("Visualization")
        visualization_layout = QVBoxLayout(visualization_box)
        self.show_boundaries = QCheckBox("Show Boundaries")
        self.show_labels = QCheckBox("Show Labels")
        self.show_markers = QCheckBox("Show Markers")
        self.show_distance_map = QCheckBox("Show Distance Map")
        self.show_boundaries.setChecked(True)
        self.show_labels.setChecked(True)
        for checkbox in (self.show_boundaries, self.show_labels, self.show_markers, self.show_distance_map):
            visualization_layout.addWidget(checkbox)
            checkbox.stateChanged.connect(lambda _: self.displayOptionsChanged.emit(self.display_options()))

        self.histogram = HistogramWidget()

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Threshold", "Objects", "Avg Area", "Time (ms)"])
        self.history_table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(visualization_box)
        layout.addWidget(self.histogram)
        layout.addWidget(self.history_table)

    def display_options(self) -> dict:
        return {
            "show_boundaries": self.show_boundaries.isChecked(),
            "show_labels": self.show_labels.isChecked(),
            "show_markers": self.show_markers.isChecked(),
            "show_distance_map": self.show_distance_map.isChecked(),
        }

    def update_result(self, result: CellCounterResult | None, params: CellCounterParams | None) -> None:
        if result is None or params is None:
            for label in self.metric_labels.values():
                label.setText("-")
            self.histogram.plot_values([], title="Object Area Distribution")
            return

        self.metric_labels["Objects Detected"].setText(str(result.object_count))
        self.metric_labels["Total Area (px)"].setText(f"{result.total_area:,.0f}")
        self.metric_labels["Average Area (px)"].setText(f"{result.average_area:,.0f}")
        self.metric_labels["Min Area (px)"].setText(f"{result.min_area:,.0f}")
        self.metric_labels["Max Area (px)"].setText(f"{result.max_area:,.0f}")
        self.metric_labels["Processing Time"].setText(f"{result.processing_time_ms:.2f} ms")
        self.metric_labels["Parameters"].setText(
            f"{params.threshold_method}, G={params.gaussian_kernel}, M={params.morphology_kernel}, "
            f"DT={params.distance_threshold_ratio:.2f}, Min={params.min_object_area}"
        )
        self.histogram.plot_values(result.object_areas, title="Object Area Distribution")

    def add_history_entry(self, result: CellCounterResult, params: CellCounterParams) -> None:
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        values = [
            f"{params.distance_threshold_ratio:.2f}",
            str(result.object_count),
            f"{result.average_area:.0f}",
            f"{result.processing_time_ms:.2f}",
        ]
        for column, value in enumerate(values):
            self.history_table.setItem(row, column, QTableWidgetItem(value))

