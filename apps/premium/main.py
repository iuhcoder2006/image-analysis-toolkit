from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from apps.premium.pages.cell_counter_page import CellCounterPage
from apps.premium.pages.image_transform_page import ImageTransformPage
from shared.ui.app_shell import AppSidebar
from styles.theme import APP_STYLESHEET


class ToolkitWindow(QMainWindow):
    """Single native desktop shell hosting both image-analysis workflows."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Analysis Toolkit")
        self.resize(1536, 960)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_STYLESHEET)

        self.sidebar = AppSidebar()
        self.pages = QStackedWidget()
        self.image_page = ImageTransformPage()
        self.counter_page = CellCounterPage()
        self.pages.addWidget(self.image_page)
        self.pages.addWidget(self.counter_page)
        self.pages.addWidget(self._placeholder("History", "Completed transforms and segmentation runs will appear here."))
        self.pages.addWidget(self._placeholder("Settings", "Theme, shortcuts and performance settings will appear here."))

        shell = QWidget()
        shell.setObjectName("appShell")
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        # A horizontal layout is expressed through a nested widget to keep app-level margins at zero.
        from PySide6.QtWidgets import QHBoxLayout

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.sidebar)
        row.addWidget(self.pages, 1)
        layout.addLayout(row)
        self.setCentralWidget(shell)
        self.sidebar.pageRequested.connect(self._navigate)

    @staticmethod
    def _placeholder(title: str, message: str) -> QWidget:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QLabel

        page = QWidget()
        page.setObjectName("pageSurface")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        detail = QLabel(message)
        detail.setObjectName("metadata")
        layout.addWidget(heading, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(detail, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def _navigate(self, page: str) -> None:
        self.pages.setCurrentIndex({"image": 0, "counter": 1, "history": 2, "settings": 3}[page])


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Image Analysis Toolkit")
    window = ToolkitWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
