"""
Lumi Editor — Logo / Watermark Insertion Engine
Overlays a logo or watermark onto images with configurable position,
scale, opacity, and tiling support.
"""

import os
from enum import Enum
from PIL import Image

from core.utils import (
    discover_images,
    ensure_output_dir,
    generate_output_path,
    save_image,
    load_oriented_image,
)


# ─── Enumerations ────────────────────────────────────────────────

class LogoPosition(Enum):
    TOP_LEFT     = "Top-Left"
    TOP_RIGHT    = "Top-Right"
    BOTTOM_LEFT  = "Bottom-Left"
    BOTTOM_RIGHT = "Bottom-Right"
    CENTER       = "Center"
    TILED        = "Tiled"


# ─── Internal Helpers ────────────────────────────────────────────

def _prepare_logo(
    logo: Image.Image,
    target_width: int,
    scale_pct: float,
    opacity: float,
) -> Image.Image:
    """
    Resize the logo proportionally and apply opacity.

    Args:
        logo:          Original logo image.
        target_width:  Width of the base / target image (px).
        scale_pct:     Logo width as a percentage of the base width (1–100).
        opacity:       Alpha multiplier (0.0 – 1.0).

    Returns:
        Prepared RGBA logo image ready for compositing.
    """
    logo = logo.convert("RGBA")

    # Scale proportionally
    logo_w = max(1, int(target_width * scale_pct / 100))
    aspect  = logo.height / logo.width if logo.width else 1
    logo_h  = max(1, int(logo_w * aspect))

    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

    # Apply opacity by scaling the alpha channel
    if opacity < 1.0:
        r, g, b, a = logo.split()
        a = a.point(lambda px: int(px * opacity))
        logo = Image.merge("RGBA", (r, g, b, a))

    return logo


def _calc_position(
    base_size: tuple[int, int],
    logo_size: tuple[int, int],
    position: LogoPosition,
    padding: int,
) -> tuple[int, int]:
    """Return the (x, y) paste coordinate for the logo on the base image."""
    bw, bh = base_size
    lw, lh = logo_size

    coords = {
        LogoPosition.TOP_LEFT:     (padding, padding),
        LogoPosition.TOP_RIGHT:    (bw - lw - padding, padding),
        LogoPosition.BOTTOM_LEFT:  (padding, bh - lh - padding),
        LogoPosition.BOTTOM_RIGHT: (bw - lw - padding, bh - lh - padding),
        LogoPosition.CENTER:       ((bw - lw) // 2, (bh - lh) // 2),
    }
    return coords.get(position, coords[LogoPosition.CENTER])


def _tile_logo(
    base: Image.Image,
    logo: Image.Image,
    spacing: int,
) -> Image.Image:
    """
    Repeat the logo across the entire image in a grid pattern.

    Args:
        base:    RGBA base image.
        logo:    RGBA logo (already scaled & opacity-applied).
        spacing: Pixel gap between logo tiles.

    Returns:
        Composited RGBA image with tiled logo.
    """
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    lw, lh = logo.size
    bw, bh = base.size

    step_x = lw + spacing
    step_y = lh + spacing

    y = spacing
    while y < bh:
        x = spacing
        while x < bw:
            # Only paste if at least part of the logo is visible
            if x + lw > 0 and y + lh > 0:
                overlay.paste(logo, (x, y), logo)
            x += step_x
        y += step_y

    return Image.alpha_composite(base, overlay)


# ─── Public API ──────────────────────────────────────────────────

def insert_logo_single(
    base: Image.Image,
    logo: Image.Image,
    position: LogoPosition,
    scale_pct: float = 15.0,
    opacity: float = 1.0,
    padding: int = 10,
) -> Image.Image:
    """
    Overlay a logo onto a single base image.

    Args:
        base:      The photograph / base image.
        logo:      The logo image (PNG with transparency recommended).
        position:  Where to place the logo (or Tiled).
        scale_pct: Logo width as % of base image width (1–100).
        opacity:   Logo opacity (0.0 transparent – 1.0 opaque).
        padding:   Pixel margin from the nearest edge(s).

    Returns:
        New RGBA image with the logo composited.
    """
    base_rgba = base.convert("RGBA")
    prepared  = _prepare_logo(logo, base_rgba.width, scale_pct, opacity)

    if position == LogoPosition.TILED:
        return _tile_logo(base_rgba, prepared, padding)

    # Single placement via alpha_composite for clean blending
    overlay = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    pos = _calc_position(base_rgba.size, prepared.size, position, padding)
    overlay.paste(prepared, pos, prepared)

    return Image.alpha_composite(base_rgba, overlay)


# ─── Batch Processing ───────────────────────────────────────────

def batch_insert_logo(
    input_dir: str,
    output_dir: str,
    logo_path: str,
    position: LogoPosition,
    scale_pct: float = 15.0,
    opacity: float = 1.0,
    padding: int = 10,
    output_format: str = "same",
    quality: int = 95,
    rotation: str = "Auto (EXIF)",
    progress_callback=None,
) -> dict:
    """
    Insert a logo onto every image in *input_dir* and save to *output_dir*.

    Args:
        input_dir:         Source folder containing images.
        output_dir:        Destination folder (auto-created).
        logo_path:         Path to the logo file (PNG recommended).
        position:          LogoPosition enum member.
        scale_pct:         Logo scale as % of image width.
        opacity:           Logo opacity 0.0–1.0.
        padding:           Edge padding in pixels.
        output_format:     "same" / "jpeg" / "png" / "webp".
        quality:           JPEG / WebP quality 1–100.
        rotation:          Rotation mode ('Auto (EXIF)', 'Rotate 90° CW', etc.).
        progress_callback: Optional ``(current, total, filename, status)`` callable.

    Returns:
        Result dict: {processed, failed, errors[], total}.
    """
    images = discover_images(input_dir)
    ensure_output_dir(output_dir)

    # Load logo once with orientation handling — all images share the same source logo
    logo = load_oriented_image(logo_path).convert("RGBA")

    results = {
        "processed": 0,
        "failed":    0,
        "errors":    [],
        "total":     len(images),
    }

    for idx, img_path in enumerate(images, start=1):
        filename = os.path.basename(img_path)
        try:
            base = load_oriented_image(img_path, rotation=rotation)
            exif_data = base.getexif()
            result_img = insert_logo_single(
                base, logo, position,
                scale_pct, opacity, padding,
            )

            out_path = generate_output_path(
                img_path, output_dir, "", output_format,
            )
            save_image(result_img, out_path, output_format, quality, img_path, exif=exif_data)
            results["processed"] += 1

            if progress_callback:
                progress_callback(idx, results["total"], filename, "success")

        except Exception as exc:
            results["failed"] += 1
            results["errors"].append({"file": filename, "error": str(exc)})
            if progress_callback:
                progress_callback(idx, results["total"], filename, f"error: {exc}")

    return results
