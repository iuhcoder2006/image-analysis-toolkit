from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QTabWidget, QVBoxLayout, QWidget

from apps.cell_counter.config import APP_NAME, APP_STYLESHEET, PROJECT_OUTPUT_DIR
from apps.cell_counter.processing.object_counter import compose_overlay
from apps.cell_counter.processing.watershed import CellCounterParams, CellCounterResult, run_watershed_pipeline
from apps.cell_counter.ui.controls_panel import ControlsPanel
from apps.cell_counter.ui.explanation_panel import ExplanationPanel
from apps.cell_counter.ui.image_canvas import ImageCanvas
from apps.cell_counter.ui.pipeline_visualizer import PipelineVisualizer
from apps.cell_counter.ui.result_analysis_panel import ResultAnalysisPanel
from shared.constants import IMAGE_FILTER
from shared.image_io import load_image, save_image
from shared.image_utils import normalize_for_display
from shared.ui.file_toolbar import FileToolbar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1500, 940)
        self.setStyleSheet(APP_STYLESHEET)

        self.original_image: np.ndarray | None = None
        self.current_params = CellCounterParams()
        self.current_result: CellCounterResult | None = None
        self.current_stage = "Original"
        self.stage_images: dict[str, np.ndarray] = {}

        self.toolbar = FileToolbar(include_video=False)
        self.controls_panel = ControlsPanel()
        self.main_canvas = ImageCanvas("Original")
        self.pipeline_visualizer = PipelineVisualizer()
        self.explanation_panel = ExplanationPanel()
        self.analysis_panel = ResultAnalysisPanel()

        right_tabs = QTabWidget()
        right_tabs.addTab(self.explanation_panel, "Algorithm Explanation")
        right_tabs.addTab(self.analysis_panel, "Result Analysis")

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)
        center_layout.addWidget(self.main_canvas, 1)
        center_layout.addWidget(self.pipeline_visualizer, 0)

        content = QWidget()
        self.setCentralWidget(content)
        root_layout = QVBoxLayout(content)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)
        root_layout.addWidget(self.toolbar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        content_layout.addWidget(self.controls_panel, 0)
        content_layout.addWidget(center_widget, 1)
        content_layout.addWidget(right_tabs, 0)
        root_layout.addLayout(content_layout, 1)

        self.toolbar.openImageRequested.connect(self.open_image)
        self.toolbar.saveRequested.connect(self.save_result)
        self.toolbar.resetRequested.connect(self.reset_all)
        self.controls_panel.runRequested.connect(self.run_pipeline)
        self.controls_panel.resetRequested.connect(self.reset_controls)
        self.pipeline_visualizer.stageSelected.connect(self.select_stage)
        self.analysis_panel.displayOptionsChanged.connect(lambda _: self.refresh_stage_view())

        self.explanation_panel.update_for_stage("Original", None, self.current_params)

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Cell / Particle Image", "", IMAGE_FILTER)
        if not path:
            return
        try:
            self.original_image = load_image(path)
            self.main_canvas.set_image(self.original_image)
            self.main_canvas.set_title(f"Original - {Path(path).name}")
            self.pipeline_visualizer.set_stages({"Original": self.original_image})
            self.current_stage = "Original"
            self.current_result = None
            self.analysis_panel.update_result(None, None)
            self.explanation_panel.update_for_stage("Original", None, self.current_params)
            self.statusBar().showMessage(f"Loaded image: {Path(path).name}", 4000)
        except Exception as error:  # pragma: no cover - GUI interaction
            self._show_error(str(error))

    def save_result(self) -> None:
        if self.current_result is None:
            self._show_error("There is no watershed result to save.")
            return
        PROJECT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Segmentation Result",
            str(PROJECT_OUTPUT_DIR / "watershed_result.png"),
            IMAGE_FILTER,
        )
        if not path:
            return
        try:
            save_image(path, self.current_result.overlay)
            self.statusBar().showMessage(f"Saved result to {Path(path).name}", 4000)
        except Exception as error:  # pragma: no cover - GUI interaction
            self._show_error(str(error))

    def run_pipeline(self, params: CellCounterParams) -> None:
        if self.original_image is None:
            self._show_error("Load an image before running the watershed pipeline.")
            return
        try:
            self.current_params = params
            self.current_result = run_watershed_pipeline(self.original_image, params)
            if self.current_result.object_count == 0:
                self.statusBar().showMessage("Watershed completed but zero objects were detected.", 5000)
            self.stage_images = self._build_stage_images(self.current_result)
            self.pipeline_visualizer.set_stages(self.stage_images)
            self.current_stage = "Final Overlay"
            self.pipeline_visualizer.select_stage("Final Overlay")
            self.analysis_panel.update_result(self.current_result, self.current_params)
            self.analysis_panel.add_history_entry(self.current_result, self.current_params)
            self.explanation_panel.update_for_stage(self.current_stage, self.current_result, self.current_params)
        except Exception as error:
            self._show_error(str(error))

    def reset_all(self) -> None:
        self.current_result = None
        self.stage_images = {"Original": self.original_image} if self.original_image is not None else {}
        if self.original_image is not None:
            self.main_canvas.set_image(self.original_image)
            self.main_canvas.set_title("Original")
            self.pipeline_visualizer.set_stages(self.stage_images)
        self.analysis_panel.update_result(None, None)
        self.explanation_panel.update_for_stage("Original", None, self.current_params)

    def reset_controls(self) -> None:
        self.controls_panel.reset_defaults()

    def select_stage(self, stage: str) -> None:
        self.current_stage = stage
        self.refresh_stage_view()

    def refresh_stage_view(self) -> None:
        if not self.stage_images:
            return
        if self.current_stage == "Final Overlay" and self.current_result is not None:
            display_image = self._compose_current_overlay()
        elif self.current_stage == "Distance Transform" and self.analysis_panel.display_options()["show_distance_map"] and self.current_result is not None:
            display_image = self.current_result.normalized_distance_map
        else:
            display_image = self.stage_images.get(self.current_stage)

        self.main_canvas.set_title(self.current_stage)
        self.main_canvas.set_image(display_image)
        self.explanation_panel.update_for_stage(self.current_stage, self.current_result, self.current_params)

    def _build_stage_images(self, result: CellCounterResult) -> dict[str, np.ndarray]:
        markers_preview = normalize_for_display(result.markers_before.astype(np.float32))
        markers_preview = cv2.applyColorMap(markers_preview, cv2.COLORMAP_VIRIDIS)
        return {
            "Original": result.original,
            "Grayscale": result.grayscale,
            "Threshold": result.binary,
            "Morphology": result.morphology,
            "Distance Transform": result.normalized_distance_map,
            "Markers": markers_preview,
            "Watershed": result.marker_visualization,
            "Final Overlay": result.overlay,
        }

    def _compose_current_overlay(self) -> np.ndarray:
        assert self.current_result is not None
        options = self.analysis_panel.display_options()
        if options["show_distance_map"]:
            return self.current_result.normalized_distance_map
        return compose_overlay(
            self.current_result.original,
            self.current_result.filtered_markers,
            [marker_id for marker_id in np.unique(self.current_result.filtered_markers) if marker_id > 1],
            show_boundaries=options["show_boundaries"],
            show_labels=options["show_labels"],
            show_markers=options["show_markers"],
            marker_visualization=self.current_result.marker_visualization,
        )

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, APP_NAME, message)
