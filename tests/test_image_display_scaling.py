import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from shared.image_utils import scale_pixmap_for_viewport


def test_preview_scaling_uses_physical_pixels_for_high_dpi_display() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    scaled = scale_pixmap_for_viewport(QPixmap(400, 200), QSize(200, 200), 1.5)

    assert scaled.devicePixelRatio() == 1.5
    assert scaled.deviceIndependentSize().toSize() == QSize(200, 100)
    assert scaled.size() == QSize(300, 150)
