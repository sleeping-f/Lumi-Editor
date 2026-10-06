# Lumi Editor

**Batch Edit. Simplified.**

A desktop application for high-performance batch image processing — crop hundreds of images or insert your logo/watermark in seconds.

![Lumi Editor Logo](assets/logo.png)

---

## ⚡ Quick Start

### Option A: Run Standalone Executable (No Python Required)
You can directly run the compiled binary or the desktop shortcut:
- **Executable**: `dist\LumiEditor.exe`
- **Desktop Shortcut**: Run `create_desktop_shortcut.bat` to create an icon on your desktop.

### Option B: Run with Python
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch
python main.py
```

---

## 🛠️ Build & Maintenance Tools

We provide one-click Windows automation scripts:

- **`build_exe.bat`** — Automatically compiles all source code, assets, and dependencies into a single portable `dist\LumiEditor.exe` with your logo icon embedded.
- **`create_desktop_shortcut.bat`** — Creates a clean desktop shortcut pointing directly to Lumi Editor with the custom brand icon.

---

## ✨ System Update Engine

Lumi Editor includes a built-in software update manager:
- **In-App Check**: Click **"✨ Check Updates"** in the top header or click the version number (`v1.0.0`) in the bottom right corner.
- **Update Dialog**: Displays changelogs, release notes, and latest version status.
- **Self-Updating Engine**: On Windows, when an update is approved, Lumi Editor seamlessly downloads the new release, executes a background handoff runner, updates itself, and restarts.

---

## 🚀 Features

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

### Core Polish & UX

- **Real-Time Preview** — See the result on a sample image before processing.
- **Format Conversion** — Output as Same as Original, JPEG, PNG, or WebP.
- **Quality Control** — Adjustable JPEG/WebP quality (1–100).
- **Progress Tracking** — Gold progress bar and live image counters.
- **Non-Blocking Multi-Threaded Engine** — UI never freezes or stutters during massive batches.

---

## 📁 Project Structure

```
lumi editor/
├── dist/
│   └── LumiEditor.exe       # Standalone compiled executable
├── assets/
│   ├── logo.png             # Master brand logo
│   └── logo.ico             # Windows multi-resolution icon
├── core/
│   ├── cropper.py           # Crop engine (3 modes)
│   ├── logo_inserter.py     # Logo overlay engine (6 positions + alpha composite)
│   ├── updater.py           # Version checker & self-update runner
│   └── utils.py             # Image discovery, paths, save logic
├── tabs/
│   ├── crop_tab.py          # Batch Crop tab UI & logic
│   └── logo_tab.py          # Batch Logo tab UI & logic
├── build_exe.bat            # 1-Click .exe compiler
├── create_desktop_shortcut.bat # 1-Click desktop shortcut creator
├── main.py                  # Main application entry point & shell
├── theme.py                 # Custom brand theme & styling
├── requirements.txt
└── README.md
```

---

## 👤 Author & Credits

**Developed by Md. Farhan Sadique**  
- **Repository**: [sleeping-f/Lumi-Editor](https://github.com/sleeping-f/Lumi-Editor)
- **License**: MIT

