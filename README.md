# Image Analysis Toolkit

## Overview

This repository contains two educational desktop applications for a university image processing assignment:

- Project 1: Image Viewer
- Project 2: Cell / Particle Counter

Both applications are built with Python, PySide6, OpenCV, and NumPy. They focus on clear algorithm visualization, parameter exploration, and easy-to-explain code structure.

## Projects

### Project 1 - Image Viewer

Features:

- Open image and optional video frame input
- Zoom with multiple interpolation methods
- Rotate with angle, interpolation, and border controls
- Crop with mouse selection and numeric coordinates
- Side-by-side original and result visualization
- Algorithm explanation panel
- Result analysis panel with metrics and histograms

Run:

```bash
python -m apps.image_viewer.main
```

### Project 2 - Cell / Particle Counter

Features:

- Grayscale and Gaussian blur preprocessing
- Otsu or manual thresholding
- Morphological cleanup
- Distance transform and marker extraction
- Watershed segmentation
- Object counting and area statistics
- Pipeline stage visualization
- Parameter history for comparing runs

Run:

```bash
python -m apps.cell_counter.main
```

## Project Structure

```text
image-analysis-toolkit/
|-- apps/                # Desktop applications
|-- shared/              # Shared IO, image helpers, and reusable widgets
|-- datasets/            # Input placeholders for both projects
|-- outputs/             # Saved processing results
|-- reports/             # Jupyter notebooks for demonstrations
|-- tests/               # Unit tests for processing functions
`-- docs/                # Screenshots and diagrams
```

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Reports

Start Jupyter:

```bash
jupyter notebook
```

Then open:

- `reports/project_1/project1_image_viewer_demo.ipynb`
- `reports/project_2/project2_cell_counter_demo.ipynb`

## Dataset

Place input files in:

- `datasets/project_1/input/`
- `datasets/project_2/input/`

Supported image formats:

- `.jpg`
- `.jpeg`
- `.png`
- `.bmp`
- `.tif`
- `.tiff`

The applications handle empty dataset folders gracefully and will show a friendly message instead of crashing.

## Output

Processed files are saved to:

- `outputs/project_1/`
- `outputs/project_2/`

Users can also choose another save path from the file dialog.

