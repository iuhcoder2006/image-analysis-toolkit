from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from apps.cell_counter.processing.watershed import CellCounterParams
from shared.ui.parameter_slider import ParameterSlider


class ControlsPanel(QWidget):
    runRequested = Signal(object)
    resetRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        preprocessing_box = QGroupBox("Preprocessing")
        preprocessing_layout = QVBoxLayout(preprocessing_box)
        self.gaussian_kernel = ParameterSlider("Gaussian Kernel", 3, 15, 5, step=2, decimals=0)
        self.gaussian_sigma = ParameterSlider("Gaussian Sigma", 0.0, 5.0, 1.0, step=0.1, decimals=1)
        preprocessing_layout.addWidget(self.gaussian_kernel)
        preprocessing_layout.addWidget(self.gaussian_sigma)

        threshold_box = QGroupBox("Threshold")
        threshold_layout = QFormLayout(threshold_box)
        self.threshold_method = QComboBox()
        self.threshold_method.addItems(["Otsu", "Binary", "Adaptive"])
        self.manual_threshold = ParameterSlider("Manual Threshold", 0, 255, 127, step=1, decimals=0)
        threshold_layout.addRow("Method", self.threshold_method)
        threshold_layout.addRow(self.manual_threshold)

        morphology_box = QGroupBox("Morphology")
        morphology_layout = QVBoxLayout(morphology_box)
        self.morphology_kernel = ParameterSlider("Kernel Size", 1, 11, 3, step=2, decimals=0)
        self.opening_iterations = ParameterSlider("Opening Iterations", 1, 5, 2, step=1, decimals=0)
        self.dilation_iterations = ParameterSlider("Dilation Iterations", 1, 5, 2, step=1, decimals=0)
        morphology_layout.addWidget(self.morphology_kernel)
        morphology_layout.addWidget(self.opening_iterations)
        morphology_layout.addWidget(self.dilation_iterations)

        distance_box = QGroupBox("Distance Transform")
        distance_layout = QFormLayout(distance_box)
        self.distance_type = QComboBox()
        self.distance_type.addItems(["L2", "L1", "Chessboard"])
        self.mask_size = QComboBox()
        self.mask_size.addItems(["3", "5"])
        self.distance_threshold_ratio = ParameterSlider("Foreground Threshold", 0.1, 0.9, 0.4, step=0.05, decimals=2)
        distance_layout.addRow("Distance Type", self.distance_type)
        distance_layout.addRow("Mask Size", self.mask_size)
        distance_layout.addRow(self.distance_threshold_ratio)

        filter_box = QGroupBox("Object Filter")
        filter_layout = QVBoxLayout(filter_box)
        self.min_object_area = ParameterSlider("Min Object Area", 5, 1000, 50, step=5, decimals=0)
        filter_layout.addWidget(self.min_object_area)

        button_row = QHBoxLayout()
        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("accentButton")
        self.reset_button = QPushButton("Reset")
        button_row.addWidget(self.run_button)
        button_row.addWidget(self.reset_button)

        layout.addWidget(preprocessing_box)
        layout.addWidget(threshold_box)
        layout.addWidget(morphology_box)
        layout.addWidget(distance_box)
        layout.addWidget(filter_box)
        layout.addLayout(button_row)
        layout.addStretch(1)

        self.threshold_method.currentTextChanged.connect(self._update_threshold_help)
        self.run_button.clicked.connect(lambda: self.runRequested.emit(self.current_parameters()))
        self.reset_button.clicked.connect(self.resetRequested.emit)
        self._update_threshold_help()

    def current_parameters(self) -> CellCounterParams:
        return CellCounterParams(
            gaussian_kernel=int(self.gaussian_kernel.value()),
            gaussian_sigma=float(self.gaussian_sigma.value()),
            threshold_method=self.threshold_method.currentText(),
            manual_threshold=int(self.manual_threshold.value()),
            morphology_kernel=int(self.morphology_kernel.value()),
            opening_iterations=int(self.opening_iterations.value()),
            dilation_iterations=int(self.dilation_iterations.value()),
            distance_type=self.distance_type.currentText(),
            mask_size=int(self.mask_size.currentText()),
            distance_threshold_ratio=float(self.distance_threshold_ratio.value()),
            min_object_area=int(self.min_object_area.value()),
        )

    def reset_defaults(self) -> None:
        defaults = CellCounterParams()
        self.gaussian_kernel.set_value(defaults.gaussian_kernel)
        self.gaussian_sigma.set_value(defaults.gaussian_sigma)
        self.threshold_method.setCurrentText(defaults.threshold_method)
        self.manual_threshold.set_value(defaults.manual_threshold)
        self.morphology_kernel.set_value(defaults.morphology_kernel)
        self.opening_iterations.set_value(defaults.opening_iterations)
        self.dilation_iterations.set_value(defaults.dilation_iterations)
        self.distance_type.setCurrentText(defaults.distance_type)
        self.mask_size.setCurrentText(str(defaults.mask_size))
        self.distance_threshold_ratio.set_value(defaults.distance_threshold_ratio)
        self.min_object_area.set_value(defaults.min_object_area)
        self._update_threshold_help()

    def _update_threshold_help(self) -> None:
        self.manual_threshold.setVisible(self.threshold_method.currentText() == "Binary")

