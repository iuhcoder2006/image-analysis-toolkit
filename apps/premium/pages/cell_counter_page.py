from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from apps.cell_counter.processing.object_counter import compose_overlay
from apps.cell_counter.processing.watershed import CellCounterParams, CellCounterResult
from apps.premium.components import InlineAlert, MetricCard
from apps.premium.progressive_segmentation import ProgressiveSegmentationWorker
from shared.constants import IMAGE_FILTER
from shared.image_io import load_image, save_image
from shared.image_utils import normalize_for_display
from shared.ui.app_shell import StatusStrip
from shared.ui.histogram_widget import HistogramWidget
from shared.ui.image_viewport import ImageViewport
from shared.ui.parameter_slider import ParameterSlider
from shared.ui.segmented_control import SegmentedControl


STAGES = ("Original", "Grayscale", "Threshold", "Morphology", "Distance Transform", "Markers", "Watershed", "Final Overlay")


class PipelineStepper(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self._buttons: dict[str, QPushButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(5)
        for index, stage in enumerate(STAGES, 1):
            button = QPushButton(f"{index}\n{stage}")
            button.setCheckable(True)
            button.setEnabled(False)
            button.setFixedHeight(52)
            button.setMinimumWidth(78)
            button.setObjectName("segmentButton")
            self._buttons[stage] = button
            layout.addWidget(button)
        layout.addStretch(1)

    def on_stage_selected(self, callback) -> None:
        for stage, button in self._buttons.items():
            button.clicked.connect(lambda _checked=False, name=stage: callback(name))

    def set_ready(self, stage: str) -> None:
        button = self._buttons[stage]
        button.setEnabled(True)
        button.setText(button.text().replace("\n", " ✓\n", 1) if "✓" not in button.text() else button.text())

    def set_selected(self, stage: str) -> None:
        for name, button in self._buttons.items():
            button.setChecked(name == stage)

    def reset(self) -> None:
        for index, stage in enumerate(STAGES, 1):
            button = self._buttons[stage]
            button.setEnabled(False)
            button.setChecked(False)
            button.setText(f"{index}\n{stage}")


class CellCounterPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageSurface")
        self.original_image: np.ndarray | None = None
        self.current_result: CellCounterResult | None = None
        self.current_params = CellCounterParams()
        self.stage_images: dict[str, np.ndarray] = {}
        self.current_stage = "Original"
        self._thread: QThread | None = None
        self.viewport = ImageViewport("Load a cell / particle image")
        self.stepper = PipelineStepper()
        self.stepper.on_stage_selected(self.select_stage)
        self.status_strip = StatusStrip()
        self.parameters = self._build_parameters()
        self.right_tabs = self._build_right_tabs()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(10)
        layout.addWidget(self._build_toolbar())
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._wrap_scroll(self.parameters))
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)
        center_layout.addWidget(self.viewport, 1)
        center_layout.addWidget(self.stepper)
        splitter.addWidget(center)
        splitter.addWidget(self.right_tabs)
        splitter.setSizes([315, 780, 330])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.status_strip)

    @staticmethod
    def _wrap_scroll(widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def _build_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topToolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title = QLabel("Cell / Particle Counter")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Scientific imaging workstation  ·  watershed segmentation")
        subtitle.setObjectName("metadata")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        layout.addStretch(1)
        for text, handler, accent in (("Open Image", self.open_image, False), ("Save Result", self.save_result, False), ("Reset", self.reset_all, False)):
            button = QPushButton(text)
            if accent:
                button.setObjectName("accentButton")
            button.clicked.connect(handler)
            layout.addWidget(button)
        return bar

    def _build_parameters(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QLabel("PIPELINE PARAMETERS")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        self.gaussian_kernel = ParameterSlider("Gaussian Kernel", 3, 15, 5, 2, 0)
        self.gaussian_sigma = ParameterSlider("Gaussian Sigma", 0, 5, 1, .1, 1)
        self.threshold_method = SegmentedControl(["Otsu", "Binary", "Adaptive"])
        self.manual_threshold = ParameterSlider("Manual Threshold", 0, 255, 127, 1, 0)
        self.morphology_kernel = ParameterSlider("Kernel Size", 1, 11, 3, 2, 0)
        self.opening_iterations = ParameterSlider("Opening Iterations", 1, 5, 2, 1, 0)
        self.dilation_iterations = ParameterSlider("Dilation Iterations", 1, 5, 2, 1, 0)
        self.distance_type = SegmentedControl(["L2", "L1", "Chessboard"])
        self.mask_size = SegmentedControl(["3", "5"])
        self.mask_size.set_current_text("5")
        self.foreground_threshold = ParameterSlider("Foreground Threshold", .1, .9, .4, .05, 2)
        self.min_area = ParameterSlider("Min Object Area", 5, 1000, 50, 5, 0)
        for title, widgets in (
            ("Preprocessing", (self.gaussian_kernel, self.gaussian_sigma)),
            ("Threshold", (self.threshold_method, self.manual_threshold)),
            ("Morphology", (self.morphology_kernel, self.opening_iterations, self.dilation_iterations)),
            ("Distance Transform", (self.distance_type, self.mask_size, self.foreground_threshold)),
            ("Object Filter", (self.min_area,)),
        ):
            card = QFrame()
            card.setObjectName("panel")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            label = QLabel(title)
            label.setObjectName("sectionTitle")
            card_layout.addWidget(label)
            for widget in widgets:
                card_layout.addWidget(widget)
            layout.addWidget(card)
        self.parameter_alert = InlineAlert()
        self.run_button = QPushButton("▶  Run Segmentation")
        self.run_button.setObjectName("runButton")
        self.run_button.setMinimumHeight(44)
        defaults = QPushButton("Restore Defaults")
        layout.addWidget(self.parameter_alert)
        layout.addWidget(self.run_button)
        layout.addWidget(defaults)
        layout.addStretch(1)
        self.threshold_method.currentTextChanged.connect(self._threshold_method_changed)
        self.run_button.clicked.connect(self.run_pipeline)
        defaults.clicked.connect(self.reset_parameters)
        self._threshold_method_changed("Otsu")
        return panel

    def _build_right_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        analysis = QWidget()
        analysis_layout = QVBoxLayout(analysis)
        analysis_layout.setContentsMargins(10, 10, 10, 10)
        analysis_layout.setSpacing(8)
        grid = QGridLayout()
        self.cards = {
            "Objects": MetricCard("OBJECTS DETECTED"),
            "Total": MetricCard("TOTAL AREA"),
            "Average": MetricCard("AVERAGE AREA"),
            "Time": MetricCard("PROCESSING TIME"),
        }
        for index, card in enumerate(self.cards.values()):
            grid.addWidget(card, index // 2, index % 2)
        analysis_layout.addLayout(grid)
        self.show_boundaries = QPushButton("Boundaries")
        self.show_labels = QPushButton("Labels")
        self.show_markers = QPushButton("Markers")
        self.show_distance = QPushButton("Distance Map")
        options = QHBoxLayout()
        for button, checked in ((self.show_boundaries, True), (self.show_labels, True), (self.show_markers, False), (self.show_distance, False)):
            button.setCheckable(True)
            button.setChecked(checked)
            button.clicked.connect(lambda: self.select_stage("Final Overlay"))
            options.addWidget(button)
        analysis_layout.addWidget(QLabel("Visualization"))
        analysis_layout.addLayout(options)
        self.histogram = HistogramWidget()
        analysis_layout.addWidget(self.histogram, 1)
        explanation = QLabel("Select a completed stage to inspect its input, output, purpose and active parameters.")
        explanation.setWordWrap(True)
        explanation.setAlignment(Qt.AlignmentFlag.AlignTop)
        explanation.setContentsMargins(12, 12, 12, 12)
        self.explanation = explanation
        history = QLabel("No completed runs yet.")
        history.setObjectName("metadata")
        history.setAlignment(Qt.AlignmentFlag.AlignTop)
        history.setContentsMargins(12, 12, 12, 12)
        self.history = history
        tabs.addTab(analysis, "Analysis")
        tabs.addTab(explanation, "Algorithm")
        tabs.addTab(history, "History")
        return tabs

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Cell / Particle Image", "", IMAGE_FILTER)
        if not path:
            return
        try:
            self.original_image = load_image(path)
        except Exception as error:  # pragma: no cover
            self.status_strip.set_status(f"Could not read image: {error}")
            return
        self.current_result = None
        self.stage_images = {"Original": self.original_image}
        self.stepper.reset()
        self.stepper.set_ready("Original")
        self.select_stage("Original")
        self.status_strip.set_status(f"Ready  ·  {Path(path).name}  ·  {self.original_image.shape[1]} × {self.original_image.shape[0]}")

    def save_result(self) -> None:
        if self.current_result is None:
            self.status_strip.set_status("No segmentation result to save")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Segmentation", "outputs/watershed_result.png", IMAGE_FILTER)
        if not path:
            return
        save_image(path, self.current_result.overlay)
        self.status_strip.set_status(f"Saved segmentation  ·  {Path(path).name}")

    def reset_all(self) -> None:
        self.current_result = None
        if self.original_image is not None:
            self.stage_images = {"Original": self.original_image}
            self.stepper.reset()
            self.stepper.set_ready("Original")
            self.select_stage("Original")
        self.status_strip.set_status("Ready  ·  segmentation reset")

    def reset_parameters(self) -> None:
        defaults = CellCounterParams()
        self.gaussian_kernel.set_value(defaults.gaussian_kernel)
        self.gaussian_sigma.set_value(defaults.gaussian_sigma)
        self.threshold_method.set_current_text(defaults.threshold_method)
        self.manual_threshold.set_value(defaults.manual_threshold)
        self.morphology_kernel.set_value(defaults.morphology_kernel)
        self.opening_iterations.set_value(defaults.opening_iterations)
        self.dilation_iterations.set_value(defaults.dilation_iterations)
        self.distance_type.set_current_text(defaults.distance_type)
        self.mask_size.set_current_text(str(defaults.mask_size))
        self.foreground_threshold.set_value(defaults.distance_threshold_ratio)
        self.min_area.set_value(defaults.min_object_area)

    def _threshold_method_changed(self, method: str) -> None:
        self.manual_threshold.setVisible(method == "Binary")

    def _parameters(self) -> CellCounterParams:
        return CellCounterParams(
            gaussian_kernel=int(self.gaussian_kernel.value()) | 1,
            gaussian_sigma=self.gaussian_sigma.value(),
            threshold_method=self.threshold_method.current_text(),
            manual_threshold=int(self.manual_threshold.value()),
            morphology_kernel=int(self.morphology_kernel.value()) | 1,
            opening_iterations=int(self.opening_iterations.value()),
            dilation_iterations=int(self.dilation_iterations.value()),
            distance_type=self.distance_type.current_text(),
            mask_size=int(self.mask_size.current_text()),
            distance_threshold_ratio=self.foreground_threshold.value(),
            min_object_area=int(self.min_area.value()),
        )

    def run_pipeline(self) -> None:
        if self.original_image is None or self._thread is not None:
            return
        self.current_params = self._parameters()
        self.stage_images = {"Original": self.original_image}
        self.stepper.reset()
        self.stepper.set_ready("Original")
        self.run_button.setEnabled(False)
        self.status_strip.set_status("Processing pipeline…")
        thread = QThread(self)
        worker = ProgressiveSegmentationWorker()
        worker.moveToThread(thread)
        thread.started.connect(lambda: worker.run(self.original_image.copy(), self.current_params))
        worker.stage_ready.connect(self._stage_ready)
        worker.finished.connect(self._segmentation_finished)
        worker.failed.connect(self._segmentation_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._thread_finished)
        self._thread = thread
        thread.start()

    def _stage_ready(self, stage: str, image: np.ndarray) -> None:
        if stage == "Markers":
            preview = normalize_for_display(image.astype(np.float32))
            image = cv2.applyColorMap(preview, cv2.COLORMAP_VIRIDIS)
        self.stage_images[stage] = image
        self.stepper.set_ready(stage)
        self.status_strip.set_status(f"Stage {STAGES.index(stage) + 1}/{len(STAGES)}  ·  {stage}")

    def _segmentation_finished(self, result: CellCounterResult) -> None:
        self.current_result = result
        self.current_stage = "Final Overlay"
        self.select_stage("Final Overlay")
        self.cards["Objects"].set_value(str(result.object_count))
        self.cards["Total"].set_value(f"{result.total_area:,.0f} px²")
        self.cards["Average"].set_value(f"{result.average_area:,.1f} px²")
        self.cards["Time"].set_value(f"{result.processing_time_ms:.0f} ms")
        self.histogram.plot_values(result.object_areas, "Object Area Distribution")
        self.history.setText(f"Latest run\n{self.current_params.threshold_method}  ·  {result.object_count} objects  ·  {result.average_area:.1f} px² average  ·  {result.processing_time_ms:.0f} ms")
        if result.object_count == 0:
            self.parameter_alert.show_message("No matching objects found. Try reducing Min Object Area or inspect Threshold.")
        else:
            self.parameter_alert.clear()
        self.status_strip.set_status(f"Pipeline complete  ·  {result.object_count} objects  ·  {result.processing_time_ms:.0f} ms")

    def _segmentation_failed(self, message: str) -> None:
        self.status_strip.set_status(f"Segmentation error: {message}")

    def _thread_finished(self) -> None:
        thread = self._thread
        self._thread = None
        self.run_button.setEnabled(True)
        if thread is not None:
            thread.deleteLater()

    def select_stage(self, stage: str) -> None:
        if stage not in self.stage_images:
            return
        self.current_stage = stage
        self.stepper.set_selected(stage)
        image = self.stage_images[stage]
        if stage == "Final Overlay" and self.current_result is not None:
            image = self._overlay_image()
        self.viewport.set_title(stage)
        self.viewport.set_image(image)
        self._update_explanation(stage)

    def _overlay_image(self) -> np.ndarray:
        assert self.current_result is not None
        if self.show_distance.isChecked():
            return self.current_result.normalized_distance_map
        return compose_overlay(
            self.current_result.original,
            self.current_result.filtered_markers,
            [marker for marker in np.unique(self.current_result.filtered_markers) if marker > 1],
            show_boundaries=self.show_boundaries.isChecked(),
            show_labels=self.show_labels.isChecked(),
            show_markers=self.show_markers.isChecked(),
            marker_visualization=self.current_result.marker_visualization,
        )

    def _update_explanation(self, stage: str) -> None:
        detail = {
            "Original": "Input image used as the source for every processing stage.",
            "Grayscale": "Input: color image. Output: one intensity channel used for thresholding.",
            "Threshold": f"Input: blurred grayscale image. Output: binary foreground mask. Method: {self.current_params.threshold_method}.",
            "Morphology": "Opening removes isolated noise; dilation estimates the sure background.",
            "Distance Transform": f"Input: binary foreground. Output: distance map. Type: {self.current_params.distance_type}, mask: {self.current_params.mask_size}, threshold: {self.current_params.distance_threshold_ratio:.2f}.",
            "Markers": "Connected foreground components become seeds for watershed flooding.",
            "Watershed": "Markers flood across the distance landscape. Boundaries emerge where regions meet.",
            "Final Overlay": "The final image combines the original data, segmentation boundaries and optional labels/markers.",
        }[stage]
        self.explanation.setText(f"<h3>{stage}</h3><p>{detail}</p>")
