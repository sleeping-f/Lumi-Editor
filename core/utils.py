"""
Lumi Editor — Shared Utilities
Common functions for image discovery, path handling, and file saving.
"""

import os
from pathlib import Path
from PIL import Image


# ─── Supported Formats ───────────────────────────────────────────

SUPPORTED_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.bmp',
    '.tiff', '.tif', '.webp'
})


# ─── Image Discovery ─────────────────────────────────────────────

def discover_images(folder: str) -> list[str]:
    """
    Find all supported image files in a folder (non-recursive, sorted).

    Args:
        folder: Absolute path to the directory to search.

    Returns:
        Sorted list of absolute paths to supported image files.

    Raises:
        FileNotFoundError: If the folder doesn't exist.
        NotADirectoryError: If the path is not a directory.
    """
    folder_path = Path(folder)

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    images = []
    for entry in sorted(folder_path.iterdir()):
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(str(entry.resolve()))

    return images


# ─── Path Helpers ─────────────────────────────────────────────────

def ensure_output_dir(path: str) -> str:
    """
    Create the output directory (and parents) if it doesn't exist.

    Returns:
        Normalized absolute path string.
    """
    out = Path(path).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return str(out)


def generate_output_path(
    input_path: str,
    output_dir: str,
    suffix: str = "",
    output_format: str = "same"
) -> str:
    """
    Build the output file path, optionally changing format or adding a suffix.

    Args:
        input_path:    Original image path.
        output_dir:    Target directory for output.
        suffix:        String appended before the extension (e.g. "_cropped").
        output_format: "same" keeps the original extension;
                       "jpeg" / "png" / "webp" changes it.

    Returns:
        Full output file path.
    """
    stem = Path(input_path).stem

    if output_format == "same":
        ext = Path(input_path).suffix
    else:
        ext_map = {
            "jpeg": ".jpg",
            "png":  ".png",
            "webp": ".webp",
            "bmp":  ".bmp",
            "tiff": ".tiff",
        }
        ext = ext_map.get(output_format.lower(), Path(input_path).suffix)

    filename = f"{stem}{suffix}{ext}"
    return str(Path(output_dir) / filename)


# ─── Image Saving ────────────────────────────────────────────────

def save_image(
    img: Image.Image,
    path: str,
    output_format: str = "same",
    quality: int = 95,
    original_path: str = ""
) -> None:
    """
    Save a PIL Image, handling RGBA → RGB conversion for JPEG output.

    Args:
        img:             PIL Image to save.
        path:            Destination file path.
        output_format:   "same" / "jpeg" / "png" / "webp".
        quality:         JPEG / WebP quality (1–100).
        original_path:   Original file path (used for format inference when 'same').
    """
    save_path = Path(path)
    ext = save_path.suffix.lower()

    # ── JPEG: strip alpha channel ────────────────────────────────
    if ext in ('.jpg', '.jpeg'):
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

    # ── Build format-specific kwargs ─────────────────────────────
    kwargs: dict = {}
    if ext in ('.jpg', '.jpeg'):
        kwargs = {'quality': quality, 'optimize': True, 'subsampling': 0}
    elif ext == '.webp':
        kwargs = {'quality': quality, 'method': 4}
    elif ext == '.png':
        kwargs = {'optimize': True}

    img.save(str(save_path), **kwargs)
