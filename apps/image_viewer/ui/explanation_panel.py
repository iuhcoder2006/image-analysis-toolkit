from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class ExplanationPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text)

    def update_for_operation(self, operation: str, params: dict, metadata: dict | None = None) -> None:
        metadata = metadata or {}
        if operation == "Zoom":
            html = f"""
            <h3>Algorithm: Image Scaling</h3>
            <p><b>Current parameters</b><br>Scale: {params.get("scale", 1.0):.2f}x<br>
            Interpolation: {params.get("interpolation", "Bilinear")}</p>
            <p><b>Concept</b><br>Zoom changes the image size by resampling pixels on a larger or smaller grid.</p>
            <p><b>Methods</b><br>
            Nearest Neighbor: fastest, keeps blocky pixels.<br>
            Bilinear: averages nearby pixels for smoother results.<br>
            Bicubic: uses a larger neighborhood for smoother but more expensive output.</p>
            <p><b>Formula idea</b><br>For each output pixel, the algorithm maps back to a source coordinate in the original image and interpolates a value.</p>
            <p><b>Effects</b><br>High zoom may reveal interpolation artifacts. Low zoom may remove fine detail.</p>
            """
        elif operation == "Rotate":
            matrix = metadata.get("matrix")
            matrix_text = ""
            if isinstance(matrix, np.ndarray):
                matrix_text = "<pre>" + "\n".join("  ".join(f"{value:8.3f}" for value in row) for row in matrix) + "</pre>"
            html = f"""
            <h3>Algorithm: Affine Rotation</h3>
            <p><b>Current parameters</b><br>Angle: {params.get("angle", 0):.0f}°<br>
            Interpolation: {params.get("interpolation", "Bilinear")}<br>
            Border mode: {params.get("border_mode", "Constant Black")}</p>
            <p><b>Concept</b><br>Rotation turns the image around its center using an affine transform.</p>
            <p><b>Implementation</b><br>OpenCV uses <code>cv2.getRotationMatrix2D</code> to compute the matrix and <code>cv2.warpAffine</code> to resample pixels.</p>
            <p><b>Rotation matrix</b>{matrix_text}</p>
            <p><b>Interpretation</b><br>The matrix includes cosine and sine terms for the angle plus translation terms that keep the rotation centered.</p>
            <p><b>Border handling</b><br>Constant fills empty areas with black, Replicate extends edge pixels, and Reflect mirrors nearby content.</p>
            """
        else:
            x = params.get("x", 0)
            y = params.get("y", 0)
            width = params.get("width", 0)
            height = params.get("height", 0)
            html = f"""
            <h3>Algorithm: Crop by NumPy Slicing</h3>
            <p><b>Current parameters</b><br>X: {x}, Y: {y}, Width: {width}, Height: {height}</p>
            <p><b>Concept</b><br>Crop keeps only a selected rectangular region of the image.</p>
            <p><b>Implementation</b><br>NumPy slicing uses <code>image[y1:y2, x1:x2]</code>.</p>
            <p><b>Coordinate system</b><br>X increases from left to right. Y increases from top to bottom.</p>
            <p><b>Interpretation</b><br>Smaller crop regions focus attention on detail and reduce the retained percentage of the original image.</p>
            """
        self.text.setHtml(html)

