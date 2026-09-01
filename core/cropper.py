"""
Lumi Editor — Crop Engine
Three cropping modes: exact pixels, aspect ratio, and percentage trim.
Each mode can process a single image or an entire folder in batch.
"""

import os
from enum import Enum
from PIL import Image

from core.utils import (
    discover_images,
    ensure_output_dir,
    generate_output_path,
    save_image,
)


# ─── Enumerations ────────────────────────────────────────────────

class CropMode(Enum):
    EXACT_PIXELS    = "Exact Pixels"
    ASPECT_RATIO    = "Aspect Ratio"
    PERCENTAGE_TRIM = "Percentage Trim"


# ─── Single-Image Crop Functions ─────────────────────────────────

def crop_exact(
    img: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> Image.Image:
    """
    Crop to exact pixel coordinates, clamped to image bounds.

    Args:
        img:              Source image.
        left, top:        Top-left corner of the crop box (px).
        right, bottom:    Bottom-right corner of the crop box (px).

    Returns:
        New cropped PIL Image.

    Raises:
        ValueError: If the resulting region has zero area.
    """
    w, h = img.size

    # Clamp to image bounds
    left   = max(0, min(left, w))
    top    = max(0, min(top, h))
    right  = max(0, min(right, w))
    bottom = max(0, min(bottom, h))

    if right <= left or bottom <= top:
        raise ValueError(
            f"Crop box ({left}, {top}, {right}, {bottom}) results in "
            f"zero-area region for image size {w}×{h}."
        )

    return img.crop((left, top, right, bottom))


def crop_aspect_ratio(
    img: Image.Image,
    ratio_w: float,
    ratio_h: float,
    anchor: str = "Center",
) -> Image.Image:
    """
    Crop to the largest rectangle matching the given aspect ratio.

    Args:
        img:      Source image.
        ratio_w:  Width component (e.g. 16).
        ratio_h:  Height component (e.g. 9).
        anchor:   "Center", "Top-Left", "Top-Right",
                  "Bottom-Left", or "Bottom-Right".

    Returns:
        New cropped PIL Image.

    Raises:
        ValueError: If ratio components are not positive.
    """
    if ratio_w <= 0 or ratio_h <= 0:
        raise ValueError(
            f"Aspect ratio components must be positive (got {ratio_w}:{ratio_h})."
        )

    w, h = img.size
    target_ratio = ratio_w / ratio_h
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Image is wider → crop width
        new_w = int(h * target_ratio)
        new_h = h
    else:
        # Image is taller → crop height
        new_w = w
        new_h = int(w / target_ratio)

    # Ensure at least 1 px
    new_w = max(1, new_w)
    new_h = max(1, new_h)

    # Anchor calculation
    offsets = {
        "Center":       ((w - new_w) // 2, (h - new_h) // 2),
        "Top-Left":     (0, 0),
        "Top-Right":    (w - new_w, 0),
        "Bottom-Left":  (0, h - new_h),
        "Bottom-Right": (w - new_w, h - new_h),
    }
    left, top = offsets.get(anchor, offsets["Center"])

    return img.crop((left, top, left + new_w, top + new_h))


def crop_percentage(
    img: Image.Image,
    top_pct: float,
    bottom_pct: float,
    left_pct: float,
    right_pct: float,
) -> Image.Image:
    """
    Trim a percentage from each edge of the image.

    Args:
        img:        Source image.
        top_pct:    Percentage to trim from the top    (0–49).
        bottom_pct: Percentage to trim from the bottom (0–49).
        left_pct:   Percentage to trim from the left   (0–49).
        right_pct:  Percentage to trim from the right  (0–49).

    Returns:
        New cropped PIL Image.

    Raises:
        ValueError: If any percentage is out of range or combined
                    trims leave zero-area.
    """
    for name, val in [
        ("top", top_pct), ("bottom", bottom_pct),
        ("left", left_pct), ("right", right_pct),
    ]:
        if not (0 <= val < 50):
            raise ValueError(
                f"{name} trim must be between 0 and 49 % (got {val})."
            )

    if top_pct + bottom_pct >= 100:
        raise ValueError("Top + bottom trim must be less than 100 %.")
    if left_pct + right_pct >= 100:
        raise ValueError("Left + right trim must be less than 100 %.")

    w, h = img.size
    left   = int(w * left_pct   / 100)
    top    = int(h * top_pct    / 100)
    right  = w - int(w * right_pct / 100)
    bottom = h - int(h * bottom_pct / 100)

    return img.crop((left, top, right, bottom))


# ─── Dispatcher ──────────────────────────────────────────────────

def crop_single(
    img: Image.Image,
    mode: CropMode,
    params: dict,
) -> Image.Image:
    """
    Crop one image with the given mode and parameter dict.

    Params layout per mode:
        EXACT_PIXELS:    {left, top, right, bottom}
        ASPECT_RATIO:    {ratio_w, ratio_h, anchor}
        PERCENTAGE_TRIM: {top_pct, bottom_pct, left_pct, right_pct}
    """
    if mode == CropMode.EXACT_PIXELS:
        return crop_exact(
            img,
            int(params["left"]),
            int(params["top"]),
            int(params["right"]),
            int(params["bottom"]),
        )
    elif mode == CropMode.ASPECT_RATIO:
        return crop_aspect_ratio(
            img,
            float(params["ratio_w"]),
            float(params["ratio_h"]),
            params.get("anchor", "Center"),
        )
    elif mode == CropMode.PERCENTAGE_TRIM:
        return crop_percentage(
            img,
            float(params["top_pct"]),
            float(params["bottom_pct"]),
            float(params["left_pct"]),
            float(params["right_pct"]),
        )
    else:
        raise ValueError(f"Unknown crop mode: {mode}")


# ─── Batch Processing ───────────────────────────────────────────

def batch_crop(
    input_dir: str,
    output_dir: str,
    mode: CropMode,
    params: dict,
    output_format: str = "same",
    quality: int = 95,
    progress_callback=None,
) -> dict:
    """
    Crop every supported image in *input_dir* and save to *output_dir*.

    Args:
        input_dir:         Source folder.
        output_dir:        Destination folder (auto-created).
        mode:              CropMode enum member.
        params:            Mode-specific parameter dict (see crop_single).
        output_format:     "same" / "jpeg" / "png" / "webp".
        quality:           JPEG / WebP quality 1–100.
        progress_callback: Optional ``(current, total, filename, status)`` callable
                           invoked after each image.

    Returns:
        Result dict: {processed, failed, errors[], total}.
    """
    images = discover_images(input_dir)
    ensure_output_dir(output_dir)

    results = {
        "processed": 0,
        "failed":    0,
        "errors":    [],
        "total":     len(images),
    }

    for idx, img_path in enumerate(images, start=1):
        filename = os.path.basename(img_path)
        try:
            with Image.open(img_path) as img:
                img.load()                          # force full decode
                cropped = crop_single(img, mode, params)

            out_path = generate_output_path(
                img_path, output_dir, "", output_format,
            )
            save_image(cropped, out_path, output_format, quality, img_path)
            results["processed"] += 1

            if progress_callback:
                progress_callback(idx, results["total"], filename, "success")

        except Exception as exc:
            results["failed"] += 1
            results["errors"].append({"file": filename, "error": str(exc)})
            if progress_callback:
                progress_callback(idx, results["total"], filename, f"error: {exc}")

    return results
