# Lumi Editor

**Batch Edit. Simplified.**

A desktop application for batch image processing — crop hundreds of images or insert your logo/watermark in seconds.

![Lumi Editor Logo](assets/logo.png)

---

## Quick Start

```bash
# 1. Install the only dependency
pip install Pillow

# 2. Launch
python main.py
```

---

## Features

### ✂ Batch Crop

Three cropping modes to cover every workflow:

| Mode | Description |
|------|-------------|
| **Exact Pixels** | Crop to specific `(left, top, right, bottom)` coordinates |
| **Aspect Ratio** | Crop to 1:1, 4:3, 16:9, 9:16, or any custom ratio with anchor control |
| **Percentage Trim** | Trim a percentage from each edge (e.g., 10% from all sides) |

### 🖼 Batch Logo / Watermark

Insert your logo onto every image with full control:

| Setting | Range |
|---------|-------|
| **Position** | Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center, or Tiled |
| **Scale** | 1–80% of image width |
| **Opacity** | 5–100% |
| **Padding** | 0–500px from nearest edge |

### Common Features

- **Preview** — See the result on a sample image before processing
- **Format conversion** — Output as Same, JPEG, PNG, or WebP
- **Quality control** — Adjustable JPEG/WebP quality (1–100)
- **Progress tracking** — Live progress bar and image count
- **Non-blocking UI** — Processing runs in a background thread

---

## Supported Formats

JPEG, PNG, BMP, TIFF, WebP — all supported out of the box via Pillow.

---

## Project Structure

```
lumi editor/
├── main.py              # Entry point — run this
├── theme.py             # Custom UI theme (colors, fonts, tooltips)
├── tabs/
│   ├── crop_tab.py      # Batch Crop tab UI & logic
│   └── logo_tab.py      # Batch Logo tab UI & logic
├── core/
│   ├── utils.py         # Image discovery, path helpers, save logic
│   ├── cropper.py       # Crop engine (3 modes)
│   └── logo_inserter.py # Logo overlay engine (6 positions)
├── assets/
│   └── logo.png         # App logo
├── requirements.txt
└── README.md
```

---

## Requirements

- **Python 3.10+**
- **Pillow 12+** (`pip install Pillow`)
- **Tkinter** (bundled with standard Python on Windows)
