from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from apps.premium.components import Filmstrip, InlineAlert
from apps.premium.workers import TransformRequest, TransformWorker
from shared.constants import IMAGE_FILTER, VIDEO_FILTER
from shared.image_io import load_image, save_image
from shared.ui.app_shell import StatusStrip
from shared.ui.histogram_widget import HistogramWidget
from shared.ui.image_viewport import ImageViewport
from shared.ui.parameter_slider import ParameterSlider
from shared.ui.segmented_control import SegmentedControl


class ImageTransformPage(QWidget):
    """Creative image editor page. Processing remains isolated from the UI thread."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageSurface")
        self.original_image: np.ndarray | None = None
        self.result_image: np.ndarray | None = None
        self._source_name = ""
        self._generation = 0
        self._pending_request: TransformRequest | None = None
        self._worker_thread: QThread | None = None
        self._last_metadata: dict = {}
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(100)
        self._debounce.timeout.connect(self._start_processing)

        self.original_canvas = ImageViewport("Original")
        self.result_canvas = ImageViewport("Result")
        self.original_canvas.cropRectChanged.connect(self._crop_selected)
        self.controls = self._build_controls()
        self.analysis_tabs = self._build_analysis()
        self.status_strip = StatusStrip()
        self.filmstrip = Filmstrip()
        self.filmstrip.open_requested.connect(self.open_image)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 10)
        root.setSpacing(10)
        root.addWidget(self._build_toolbar())
        editor = QSplitter(Qt.Orientation.Horizontal)
        editor.setChildrenCollapsible(False)
        editor.addWidget(self.original_canvas)
        editor.addWidget(self.result_canvas)
        editor.addWidget(self._build_right_panel())
        editor.setStretchFactor(0, 31)
        editor.setStretchFactor(1, 31)
        editor.setStretchFactor(2, 34)
        editor.setSizes([480, 480, 380])
        root.addWidget(editor, 1)
        root.addWidget(self.filmstrip)
        root.addWidget(self.status_strip)

    def _build_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topToolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        heading = QLabel("Image Transform Studio")
        heading.setObjectName("pageTitle")
        subtitle = QLabel("Creative image editor  ·  original and result always in view")
        subtitle.setObjectName("metadata")
        titles.addWidget(heading)
        titles.addWidget(subtitle)
        layout.addLayout(titles)
        layout.addStretch(1)
        for label, action, accent in (
            ("Open Image", self.open_image, False),
            ("Open Video", self.open_video, False),
            ("Save Result", self.save_result, True),
            ("Reset", self.reset_all, False),
        ):
            button = QPushButton(label)
            if accent:
                button.setObjectName("accentButton")
            button.clicked.connect(action)
            layout.addWidget(button)
            if label == "Save Result":
                self.save_button = button
        self.save_button.setEnabled(False)
        return bar

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("TRANSFORM TOOL")
        label.setObjectName("sectionTitle")
        self.tool_control = SegmentedControl(["Zoom", "Rotate", "Crop"])
        self.stack = QStackedWidget()
        self.stack.addWidget(self._zoom_control())
        self.stack.addWidget(self._rotate_control())
        self.stack.addWidget(self._crop_control())
        layout.addWidget(label)
        layout.addWidget(self.tool_control)
        layout.addWidget(self.stack)
        layout.addStretch(1)
        self.tool_control.currentTextChanged.connect(self._tool_changed)
        return panel

    def _zoom_control(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        value = QLabel("1.00×")
        value.setObjectName("kpiValue")
        self.zoom_value = value
        self.zoom_slider = ParameterSlider("Scale", 0.25, 4.0, 1.0, 0.05, 2)
        self.zoom_interpolation = SegmentedControl(["Nearest", "Bilinear", "Bicubic"])
        self.zoom_interpolation.set_current_text("Bicubic")
        note = QLabel("Bicubic preserves a smoother image when enlarging.")
        note.setObjectName("metadata")
        note.setWordWrap(True)
        reset = QPushButton("Reset Zoom")
        layout.addWidget(value)
        layout.addWidget(self.zoom_slider)
        layout.addWidget(QLabel("Interpolation"))
        layout.addWidget(self.zoom_interpolation)
        layout.addWidget(note)
        layout.addWidget(reset)
        layout.addStretch(1)
        self.zoom_slider.valueChanged.connect(lambda value: self._zoom_value_changed(value))
        self.zoom_interpolation.currentTextChanged.connect(lambda _value: self._schedule_processing())
        reset.clicked.connect(lambda: self.zoom_slider.set_value(1.0))
        return page

    def _rotate_control(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.rotation_value = QLabel("+0°")
        self.rotation_value.setObjectName("kpiValue")
        self.rotate_slider = ParameterSlider("Angle", -180, 180, 0, 1, 0)
        self.rotate_interpolation = SegmentedControl(["Nearest", "Bilinear", "Bicubic"])
        self.rotate_interpolation.set_current_text("Bicubic")
        self.border_mode = SegmentedControl(["Black", "Replicate", "Reflect"])
        shortcuts = QGridLayout()
        for index, (label, delta) in enumerate((("−90°", -90), ("+90°", 90), ("180°", 180), ("Reset", None))):
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, change=delta: self._rotate_nudge(change))
            shortcuts.addWidget(button, index // 2, index % 2)
        self.clip_warning = InlineAlert()
        layout.addWidget(self.rotation_value)
        layout.addWidget(self.rotate_slider)
        layout.addWidget(QLabel("Interpolation"))
        layout.addWidget(self.rotate_interpolation)
        layout.addWidget(QLabel("Border mode"))
        layout.addWidget(self.border_mode)
        layout.addLayout(shortcuts)
        layout.addWidget(self.clip_warning)
        layout.addStretch(1)
        self.rotate_slider.valueChanged.connect(self._rotate_value_changed)
        self.rotate_interpolation.currentTextChanged.connect(lambda _value: self._schedule_processing())
        self.border_mode.currentTextChanged.connect(lambda _value: self._schedule_processing())
        return page

    def _crop_control(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.crop_fields: dict[str, QSpinBox] = {}
        for key in ("X", "Y", "Width", "Height"):
            field = QSpinBox()
            field.setRange(0, 100000)
            self.crop_fields[key] = field
            form.addRow(key, field)
        self.retained = QLabel("Retained Area: —")
        self.retained.setObjectName("metadata")
        apply_button = QPushButton("Apply Crop")
        apply_button.setObjectName("accentButton")
        reset = QPushButton("Reset Crop")
        layout.addLayout(form)
        layout.addWidget(self.retained)
        layout.addWidget(apply_button)
        layout.addWidget(reset)
        layout.addStretch(1)
        apply_button.clicked.connect(self._apply_crop)
        reset.clicked.connect(self._reset_crop)
        return page

    def _build_analysis(self) -> QTabWidget:
        tabs = QTabWidget()
        metrics = QWidget()
        form = QFormLayout(metrics)
        self.metric_labels: dict[str, QLabel] = {}
        for key in ("Original Size", "Output Size", "Scale / Angle", "Interpolation", "Border / Clip", "Crop Area", "Processing"):
            value = QLabel("—")
            value.setObjectName("technicalValue")
            self.metric_labels[key] = value
            form.addRow(key, value)
        self.histogram = HistogramWidget()
        metrics_layout = QVBoxLayout()
        metrics_layout.setContentsMargins(12, 12, 12, 12)
        metrics_layout.addWidget(metrics)
        metrics_layout.addWidget(self.histogram, 1)
        metrics_container = QWidget()
        metrics_container.setLayout(metrics_layout)
        explanation = QLabel("Select a transform to see the principle, active parameters, and expected visual impact.")
        explanation.setWordWrap(True)
        explanation.setAlignment(Qt.AlignmentFlag.AlignTop)
        explanation.setContentsMargins(14, 14, 14, 14)
        self.explanation = explanation
        info = QLabel("No image loaded")
        info.setObjectName("metadata")
        info.setAlignment(Qt.AlignmentFlag.AlignTop)
        info.setContentsMargins(14, 14, 14, 14)
        self.info = info
        tabs.addTab(metrics_container, "Analysis")
        tabs.addTab(explanation, "Algorithm")
        tabs.addTab(info, "Image Info")
        return tabs

    def _build_right_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.controls)
        layout.addWidget(scroll, 3)
        layout.addWidget(self.analysis_tabs, 4)
        return container

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", IMAGE_FILTER)
        if path:
            self._load_source(path, load_image)

    def open_video(self) -> None:
        from shared.video_io import load_first_video_frame

        path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", VIDEO_FILTER)
        if path:
            self._load_source(path, load_first_video_frame)

    def _load_source(self, path: str, loader) -> None:
        try:
            image = loader(path)
        except Exception as error:  # pragma: no cover - UI IO path
            self.status_strip.set_status(f"Could not open image: {error}")
            return
        self.original_image = image
        self.result_image = image.copy()
        self._source_name = Path(path).name
        self.original_canvas.set_image(image)
        self.result_canvas.set_image(self.result_image)
        width, height = image.shape[1], image.shape[0]
        self.filmstrip.set_file(self._source_name, f"{width} × {height}  ·  {'RGB' if image.ndim == 3 else 'Grayscale'}")
        self.info.setText(f"{self._source_name}\n{width} × {height}\n{'3 channels' if image.ndim == 3 else '1 channel'}\nCurrent tool: {self.tool_control.current_text()}")
        self.save_button.setEnabled(True)
        self.status_strip.set_status(f"Ready  ·  {self._source_name}  ·  {width} × {height}")
        self._update_analysis({}, self.tool_control.current_text())
        self._update_explanation()

    def save_result(self) -> None:
        if self.result_image is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Result", f"outputs/{self._source_name or 'result.png'}", IMAGE_FILTER)
        if not path:
            return
        try:
            save_image(path, self.result_image)
            self.status_strip.set_status(f"Saved result  ·  {Path(path).name}")
        except Exception as error:  # pragma: no cover
            self.status_strip.set_status(f"Could not save result: {error}")

    def reset_all(self) -> None:
        if self.original_image is None:
            return
        self.result_image = self.original_image.copy()
        self.result_canvas.set_image(self.result_image)
        self.original_canvas.set_crop_rect(None)
        self.zoom_slider.set_value(1.0)
        self.rotate_slider.set_value(0)
        self._reset_crop()
        self.status_strip.set_status("Ready  ·  reset to source image")

    def _tool_changed(self, operation: str) -> None:
        self.stack.setCurrentIndex(["Zoom", "Rotate", "Crop"].index(operation))
        self.original_canvas.set_crop_enabled(operation == "Crop")
        self._update_explanation()
        if operation != "Crop":
            self._schedule_processing()

    def _zoom_value_changed(self, value: float) -> None:
        self.zoom_value.setText(f"{value:.2f}×")
        self._schedule_processing()

    def _rotate_value_changed(self, value: float) -> None:
        self.rotation_value.setText(f"{value:+.0f}°")
        self.clip_warning.show_message("A portion of the image may fall outside the output frame.") if value % 90 else self.clip_warning.clear()
        self._schedule_processing()

    def _rotate_nudge(self, delta: int | None) -> None:
        self.rotate_slider.set_value(0 if delta is None else max(-180, min(180, self.rotate_slider.value() + delta)))

    def _crop_selected(self, rect: tuple[int, int, int, int]) -> None:
        for key, value in zip(("X", "Y", "Width", "Height"), rect):
            self.crop_fields[key].setValue(value)
        if self.original_image is not None:
            retained = rect[2] * rect[3] / (self.original_image.shape[0] * self.original_image.shape[1]) * 100
            self.retained.setText(f"Retained Area: {retained:.1f}%")

    def _apply_crop(self) -> None:
        if self.original_image is None:
            return
        params = {key.lower(): field.value() for key, field in self.crop_fields.items()}
        self._queue_request("Crop", params)

    def _reset_crop(self) -> None:
        self.original_canvas.set_crop_rect(None)
        for field in self.crop_fields.values():
            field.setValue(0)
        self.retained.setText("Retained Area: —")

    def _schedule_processing(self) -> None:
        if self.original_image is None or self.tool_control.current_text() == "Crop":
            return
        self._debounce.start()

    def _start_processing(self) -> None:
        operation = self.tool_control.current_text()
        if operation == "Zoom":
            params = {"scale": self.zoom_slider.value(), "interpolation": self._interpolation(self.zoom_interpolation.current_text())}
        else:
            params = {
                "angle": self.rotate_slider.value(),
                "interpolation": self._interpolation(self.rotate_interpolation.current_text()),
                "border_mode": {"Black": "Constant Black", "Replicate": "Replicate", "Reflect": "Reflect"}[self.border_mode.current_text()],
            }
        self._queue_request(operation, params)

    def _queue_request(self, operation: str, params: dict) -> None:
        if self.original_image is None:
            return
        self._generation += 1
        self._pending_request = TransformRequest(self._generation, operation, self.original_image.copy(), params)
        if self._worker_thread is None:
            self._launch_pending_request()

    def _launch_pending_request(self) -> None:
        request = self._pending_request
        if request is None:
            return
        self._pending_request = None
        self.status_strip.set_status(f"Processing {request.operation} preview…")
        thread = QThread(self)
        worker = TransformWorker()
        worker.moveToThread(thread)
        thread.started.connect(lambda: worker.run(request))
        worker.finished.connect(self._processing_finished)
        worker.failed.connect(self._processing_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._thread_finished)
        self._worker_thread = thread
        thread.start()

    def _thread_finished(self) -> None:
        thread = self._worker_thread
        self._worker_thread = None
        if thread is not None:
            thread.deleteLater()
        if self._pending_request is not None:
            self._launch_pending_request()

    def _processing_finished(self, generation: int, result: object) -> None:
        if generation != self._generation:
            return
        self.result_image = result.image
        self.result_canvas.set_image(self.result_image)
        self._last_metadata = asdict(result)
        self._update_analysis(self._last_metadata, self.tool_control.current_text())
        self._update_explanation()
        self.status_strip.set_status(f"Ready  ·  {self.tool_control.current_text()} completed in {self._last_metadata.get('processing_time_ms', 0):.1f} ms")

    def _processing_failed(self, generation: int, message: str) -> None:
        if generation == self._generation:
            self.status_strip.set_status(f"Processing error: {message}")

    def _update_analysis(self, metadata: dict, operation: str) -> None:
        if self.original_image is None or self.result_image is None:
            return
        self.histogram.plot_images(self.original_image, self.result_image)
        original_size = f"{self.original_image.shape[1]} × {self.original_image.shape[0]}"
        output_size = f"{self.result_image.shape[1]} × {self.result_image.shape[0]}"
        values = {
            "Original Size": original_size,
            "Output Size": output_size,
            "Scale / Angle": f"{metadata.get('scale', metadata.get('angle', '—'))}{'×' if 'scale' in metadata else '°' if 'angle' in metadata else ''}",
            "Interpolation": str(metadata.get("interpolation", "—")),
            "Border / Clip": f"{metadata.get('border_mode', '—')} / {'Yes' if metadata.get('clipping_occurs') else 'No'}",
            "Crop Area": f"{metadata.get('retained_percentage', '—')}%" if operation == "Crop" else "—",
            "Processing": f"{metadata.get('processing_time_ms', 0):.2f} ms" if metadata else "—",
        }
        for key, value in values.items():
            self.metric_labels[key].setText(str(value))

    def _update_explanation(self) -> None:
        operation = self.tool_control.current_text()
        if operation == "Zoom":
            text = f"<h3>Image Scaling</h3><p><b>Current parameters</b><br>Scale: {self.zoom_slider.value():.2f}×<br>Interpolation: {self.zoom_interpolation.current_text()}</p><p><b>Effect</b><br>Resamples the source grid while keeping the original image untouched.</p>"
        elif operation == "Rotate":
            text = f"<h3>Affine Rotation</h3><p><b>Current parameters</b><br>Angle: {self.rotate_slider.value():+.0f}°<br>Border: {self.border_mode.current_text()}</p><p><b>Effect</b><br>Rotates around the image center and resamples missing pixels at the edge.</p>"
        else:
            text = "<h3>Crop Selection</h3><p>Drag a region over the original canvas. The cyan boundary describes the pixels retained in the result.</p>"
        self.explanation.setText(text)

    @staticmethod
    def _interpolation(value: str) -> str:
        return {"Nearest": "Nearest Neighbor", "Bilinear": "Bilinear", "Bicubic": "Bicubic"}[value]
