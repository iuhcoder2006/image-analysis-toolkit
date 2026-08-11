from __future__ import annotations

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from apps.cell_counter.processing.watershed import CellCounterParams, CellCounterResult


class ExplanationPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text)

    def update_for_stage(
        self,
        stage: str,
        result: CellCounterResult | None,
        params: CellCounterParams | None,
    ) -> None:
        params = params or CellCounterParams()
        if stage == "Distance Transform":
            html = f"""
            <h3>Stage: Distance Transform</h3>
            <p><b>Input</b><br>Binary foreground mask</p>
            <p><b>Output</b><br>Distance map where large values lie near object centers.</p>
            <p><b>Current max distance</b><br>{getattr(result, "max_distance", 0.0):.2f}</p>
            <p><b>Foreground threshold</b><br>{params.distance_threshold_ratio:.2f} × max distance</p>
            <p><b>Meaning</b><br>Pixels near the center of cells get larger values, which helps generate stable object seeds for watershed.</p>
            """
        elif stage == "Watershed":
            html = """
            <h3>Stage: Watershed</h3>
            <p>Imagine the grayscale image as a topographic surface.</p>
            <p>Dark regions are low elevation and bright regions are high elevation. Water grows from predefined markers, and a boundary appears when different regions meet.</p>
            <p>In segmentation, markers are object seeds, watershed expands them, and the red boundaries separate touching cells.</p>
            """
        elif stage == "Markers":
            html = """
            <h3>Stage: Marker Generation</h3>
            <p>Sure foreground marks reliable cell centers. Sure background marks non-object zones. Unknown pixels lie between them and will be resolved by watershed.</p>
            """
        elif stage == "Threshold":
            html = f"""
            <h3>Stage: Thresholding</h3>
            <p><b>Method</b><br>{params.threshold_method}</p>
            <p>Thresholding converts grayscale intensity into a binary mask. This creates the first estimate of object versus background.</p>
            """
        elif stage == "Morphology":
            html = """
            <h3>Stage: Morphology</h3>
            <p>Opening removes small noise. Dilation expands the cleaned regions to estimate sure background before marker extraction.</p>
            """
        elif stage == "Final Overlay":
            html = """
            <h3>Stage: Final Overlay</h3>
            <p>This view combines the original image with watershed boundaries and optional object labels or marker hints so the segmentation quality can be discussed visually.</p>
            """
        else:
            html = f"""
            <h3>Stage: {stage}</h3>
            <p>This stage is part of the preprocessing and segmentation pipeline used before watershed-based counting.</p>
            """
        self.text.setHtml(html)

