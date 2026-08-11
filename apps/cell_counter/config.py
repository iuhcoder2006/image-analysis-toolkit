from __future__ import annotations

from pathlib import Path

APP_NAME = "Cell / Particle Counter"
PROJECT_OUTPUT_DIR = Path("outputs/project_2")

APP_STYLESHEET = """
QWidget {
    background: #121418;
    color: #edf1f7;
    font-family: "Segoe UI";
    font-size: 13px;
}
QMainWindow, QTabWidget::pane, QGroupBox, QFrame {
    background: #171a21;
}
QGroupBox {
    border: 1px solid #2a3040;
    border-radius: 10px;
    margin-top: 8px;
    padding: 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QTabWidget::pane {
    border: 1px solid #31384a;
    border-radius: 8px;
    padding: 6px 10px;
    background: #1d2230;
}
QPushButton:hover, QComboBox:hover {
    border-color: #5b8cff;
}
QPushButton#accentButton {
    background: #3768ff;
    border-color: #3768ff;
}
QLabel#panelTitle {
    font-size: 15px;
    font-weight: 700;
}
QLabel#imageViewport {
    background: #0d0f14;
    border: 1px solid #2a3040;
    border-radius: 10px;
}
QTextEdit, QListWidget, QTableWidget {
    background: #171c27;
    border: 1px solid #2a3040;
    border-radius: 10px;
}
QHeaderView::section {
    background: #202637;
    color: #edf1f7;
    padding: 6px;
    border: none;
}
QCheckBox {
    spacing: 8px;
}
QSlider::groove:horizontal {
    border: 1px solid #2a3040;
    height: 6px;
    background: #202637;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #5b8cff;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
"""

