"""
Lumi Editor — Batch Crop Tab
Full-featured crop UI with three modes, live preview, and threaded batch processing.
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

from core.cropper import CropMode, crop_single, batch_crop
from core.utils import discover_images, load_oriented_image, ROTATION_MODES
from theme import COLORS, FONTS, ToolTip


# ═══════════════════════════════════════════════════════════════════
#  FORMAT HELPERS
# ═══════════════════════════════════════════════════════════════════

FORMAT_DISPLAY = ["Same as Original", "JPEG", "PNG", "WebP"]
FORMAT_MAP = {
    "Same as Original": "same",
    "JPEG": "jpeg",
    "PNG": "png",
    "WebP": "webp",
}


# ═══════════════════════════════════════════════════════════════════
#  CROP TAB
# ═══════════════════════════════════════════════════════════════════

class CropTab(ttk.Frame):
    """Batch-crop tab for the Lumi Editor notebook."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)

        self._queue = queue.Queue()
        self._processing = False

        # Dynamic parameter variables (replaced when mode changes)
        self._params: dict[str, tk.Variable] = {}

        self._build_ui()
        self._poll_queue()

    # ───────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Scrollable container supporting mouse wheel on any screen resolution
        canvas = tk.Canvas(self, bg=COLORS["bg_primary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        container = ttk.Frame(scrollable_frame, style="TFrame")
        container.pack(fill="both", expand=True, padx=24, pady=12)

        self._build_folders(container)
        self._spacer(container, 10)
        self._build_crop_settings(container)
        self._spacer(container, 10)
        self._build_output_settings(container)
        self._spacer(container, 14)
        self._build_actions(container)
        self._spacer(container, 8)
        self._build_progress(container)

    @staticmethod
    def _spacer(parent, height):
        ttk.Frame(parent, height=height, style="TFrame").pack(fill="x")

    # ── 1. Folder pickers ────────────────────────────────────────

    def _build_folders(self, parent):
        lf = ttk.LabelFrame(parent, text="  Source & Destination  ")
        lf.pack(fill="x")

        inner = ttk.Frame(lf, style="Card.TFrame")
        inner.pack(fill="x", padx=4, pady=2)

        # Input
        r1 = ttk.Frame(inner, style="Card.TFrame")
        r1.pack(fill="x", pady=(0, 8))
        ttk.Label(r1, text="Input Folder", width=14, style="Card.TLabel").pack(side="left")
        self._input_var = tk.StringVar()
        e1 = ttk.Entry(r1, textvariable=self._input_var)
        e1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(e1, "Folder containing the images you want to crop")
        ttk.Button(r1, text="Browse", style="Browse.TButton",
                   command=self._browse_input).pack(side="right")

        # Output
        r2 = ttk.Frame(inner, style="Card.TFrame")
        r2.pack(fill="x")
        ttk.Label(r2, text="Output Folder", width=14, style="Card.TLabel").pack(side="left")
        self._output_var = tk.StringVar()
        e2 = ttk.Entry(r2, textvariable=self._output_var)
        e2.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(e2, "Cropped images will be saved here (created automatically)")
        ttk.Button(r2, text="Browse", style="Browse.TButton",
                   command=self._browse_output).pack(side="right")

    # ── 2. Crop settings ─────────────────────────────────────────

    def _build_crop_settings(self, parent):
        lf = ttk.LabelFrame(parent, text="  Crop Settings  ")
        lf.pack(fill="x")

        inner = ttk.Frame(lf, style="Card.TFrame")
        inner.pack(fill="x", padx=4, pady=2)

        # Mode selector row
        mr = ttk.Frame(inner, style="Card.TFrame")
        mr.pack(fill="x", pady=(0, 12))
        ttk.Label(mr, text="Crop Mode", width=11, style="Card.TLabel").pack(side="left")
        self._mode_var = tk.StringVar(value=CropMode.EXACT_PIXELS.value)
        cb = ttk.Combobox(mr, textvariable=self._mode_var,
                          values=[m.value for m in CropMode],
                          state="readonly", width=16)
        cb.pack(side="left", padx=(0, 16))
        cb.bind("<<ComboboxSelected>>", self._on_mode_change)
        ToolTip(cb, "Choose how the crop region is defined")

        # Orientation / Rotation selector
        ttk.Label(mr, text="Orientation:", style="Card.TLabel").pack(side="left", padx=(0, 6))
        self._rotate_var = tk.StringVar(value=ROTATION_MODES[0])
        rcb = ttk.Combobox(mr, textvariable=self._rotate_var,
                           values=ROTATION_MODES,
                           state="readonly", width=15)
        rcb.pack(side="left")
        rcb.bind("<<ComboboxSelected>>", self._update_image_hint)
        ToolTip(rcb, "Auto (EXIF) keeps portrait photos upright. Choose 90°/180° for manual rotation.")

        # Image count hint
        self._count_hint = ttk.Label(mr, text="", style="CardSecondary.TLabel")
        self._count_hint.pack(side="right")

        # Dynamic parameters area
        self._dyn_frame = ttk.Frame(inner, style="Card.TFrame")
        self._dyn_frame.pack(fill="x")
        self._show_exact_pixels()

    # ── Mode-specific panels ─────────────────────────────────────

    def _clear_dynamic(self):
        for w in self._dyn_frame.winfo_children():
            w.destroy()
        self._params.clear()

    def _show_exact_pixels(self):
        self._clear_dynamic()
        f = ttk.Frame(self._dyn_frame, style="Card.TFrame")
        f.pack(fill="x")

        fields = [("Left", "left", 0), ("Top", "top", 0),
                  ("Right", "right", 1920), ("Bottom", "bottom", 1080)]

        for label, key, default in fields:
            col = ttk.Frame(f, style="Card.TFrame")
            col.pack(side="left", padx=(0, 20))
            ttk.Label(col, text=label, style="Card.TLabel").pack(anchor="w")
            var = tk.IntVar(value=default)
            self._params[key] = var
            ttk.Spinbox(col, from_=0, to=99999, textvariable=var,
                        width=8).pack(anchor="w", pady=(2, 0))

        ttk.Label(f, text="(pixel coordinates)",
                  style="CardSecondary.TLabel").pack(side="left", padx=(12, 0))

    def _show_aspect_ratio(self):
        self._clear_dynamic()
        f = ttk.Frame(self._dyn_frame, style="Card.TFrame")
        f.pack(fill="x")

        # Preset row
        pr = ttk.Frame(f, style="Card.TFrame")
        pr.pack(fill="x", pady=(0, 8))
        ttk.Label(pr, text="Ratio", width=8, style="Card.TLabel").pack(side="left")

        self._params["preset"] = tk.StringVar(value="16:9")
        presets = ["1:1", "4:3", "3:2", "16:9", "9:16", "3:4", "2:3", "Custom"]
        pcb = ttk.Combobox(pr, textvariable=self._params["preset"],
                           values=presets, state="readonly", width=10)
        pcb.pack(side="left", padx=(0, 16))
        pcb.bind("<<ComboboxSelected>>", self._on_ratio_preset)

        self._params["ratio_w"] = tk.DoubleVar(value=16)
        self._params["ratio_h"] = tk.DoubleVar(value=9)

        ttk.Label(pr, text="W:", style="Card.TLabel").pack(side="left")
        self._rw_spin = ttk.Spinbox(pr, from_=1, to=999,
                                    textvariable=self._params["ratio_w"],
                                    width=5, state="disabled")
        self._rw_spin.pack(side="left", padx=(4, 12))

        ttk.Label(pr, text="H:", style="Card.TLabel").pack(side="left")
        self._rh_spin = ttk.Spinbox(pr, from_=1, to=999,
                                    textvariable=self._params["ratio_h"],
                                    width=5, state="disabled")
        self._rh_spin.pack(side="left", padx=(4, 0))

        # Anchor row
        ar = ttk.Frame(f, style="Card.TFrame")
        ar.pack(fill="x")
        ttk.Label(ar, text="Anchor", width=8, style="Card.TLabel").pack(side="left")
        self._params["anchor"] = tk.StringVar(value="Center")
        acb = ttk.Combobox(ar, textvariable=self._params["anchor"],
                           values=["Center", "Top-Left", "Top-Right",
                                   "Bottom-Left", "Bottom-Right"],
                           state="readonly", width=14)
        acb.pack(side="left")
        ToolTip(acb, "Where to anchor the crop rectangle within the image")

    def _show_percentage(self):
        self._clear_dynamic()
        f = ttk.Frame(self._dyn_frame, style="Card.TFrame")
        f.pack(fill="x")

        fields = [("Top %", "top_pct", 10), ("Bottom %", "bottom_pct", 10),
                  ("Left %", "left_pct", 10), ("Right %", "right_pct", 10)]

        for label, key, default in fields:
            col = ttk.Frame(f, style="Card.TFrame")
            col.pack(side="left", padx=(0, 20))
            ttk.Label(col, text=label, style="Card.TLabel").pack(anchor="w")
            var = tk.DoubleVar(value=default)
            self._params[key] = var
            ttk.Spinbox(col, from_=0.0, to=49.0, textvariable=var,
                        width=6, increment=1.0).pack(anchor="w", pady=(2, 0))

        ttk.Label(f, text="(% trimmed from each edge)",
                  style="CardSecondary.TLabel").pack(side="left", padx=(12, 0))

    # ── 3. Output settings ───────────────────────────────────────

    def _build_output_settings(self, parent):
        lf = ttk.LabelFrame(parent, text="  Output Settings  ")
        lf.pack(fill="x")

        inner = ttk.Frame(lf, style="Card.TFrame")
        inner.pack(fill="x", padx=4, pady=2)

        row = ttk.Frame(inner, style="Card.TFrame")
        row.pack(fill="x")

        # Format
        ttk.Label(row, text="Format", width=10, style="Card.TLabel").pack(side="left")
        self._fmt_var = tk.StringVar(value=FORMAT_DISPLAY[0])
        ttk.Combobox(row, textvariable=self._fmt_var,
                     values=FORMAT_DISPLAY, state="readonly",
                     width=18).pack(side="left", padx=(0, 28))

        # Quality
        ttk.Label(row, text="Quality", style="Card.TLabel").pack(side="left", padx=(0, 8))
        self._quality_var = tk.IntVar(value=95)
        sc = ttk.Scale(row, from_=1, to=100, variable=self._quality_var,
                       orient="horizontal", command=self._on_quality)
        sc.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(sc, "JPEG / WebP output quality (1–100)")
        self._quality_lbl = ttk.Label(row, text="95", width=4,
                                      style="CardHeading.TLabel",
                                      font=FONTS["subheading"])
        self._quality_lbl.pack(side="left")

    # ── 4. Action bar ────────────────────────────────────────────

    def _build_actions(self, parent):
        bar = ttk.Frame(parent, style="TFrame")
        bar.pack(fill="x")

        self._preview_btn = ttk.Button(bar, text="👁  Preview",
                                       command=self._preview, style="TButton")
        self._preview_btn.pack(side="left")
        ToolTip(self._preview_btn, "Preview the crop on the first image in the folder")

        self._start_btn = ttk.Button(bar, text="🚀  Start Batch Crop",
                                     command=self._start_batch,
                                     style="Accent.TButton")
        self._start_btn.pack(side="right")
        ToolTip(self._start_btn, "Crop all images in the input folder")

    # ── 5. Progress ──────────────────────────────────────────────

    def _build_progress(self, parent):
        pf = ttk.Frame(parent, style="TFrame")
        pf.pack(fill="x")

        self._pbar = ttk.Progressbar(pf, orient="horizontal",
                                     mode="determinate",
                                     style="Gold.Horizontal.TProgressbar")
        self._pbar.pack(fill="x", pady=(0, 6))

        sr = ttk.Frame(pf, style="TFrame")
        sr.pack(fill="x")
        self._status = ttk.Label(sr, text="Ready", style="Status.TLabel")
        self._status.pack(side="left")
        self._counter = ttk.Label(sr, text="", style="Status.TLabel")
        self._counter.pack(side="right")

    # ───────────────────────────────────────────────────────────────
    #  EVENT HANDLERS
    # ───────────────────────────────────────────────────────────────

    def _on_mode_change(self, _event=None):
        mode = self._mode_var.get()
        if mode == CropMode.EXACT_PIXELS.value:
            self._show_exact_pixels()
        elif mode == CropMode.ASPECT_RATIO.value:
            self._show_aspect_ratio()
        elif mode == CropMode.PERCENTAGE_TRIM.value:
            self._show_percentage()

    def _on_ratio_preset(self, _event=None):
        preset = self._params["preset"].get()
        if preset == "Custom":
            self._rw_spin.configure(state="normal")
            self._rh_spin.configure(state="normal")
        else:
            self._rw_spin.configure(state="disabled")
            self._rh_spin.configure(state="disabled")
            w, h = preset.split(":")
            self._params["ratio_w"].set(float(w))
            self._params["ratio_h"].set(float(h))

    def _on_quality(self, val):
        self._quality_lbl.configure(text=str(int(float(val))))

    def _browse_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder", parent=self)
        if folder:
            self._input_var.set(folder)
            if not self._output_var.get():
                self._output_var.set(os.path.join(folder, "cropped"))
            self._update_image_hint()

    def _update_image_hint(self, _event=None):
        folder = self._input_var.get().strip()
        if not folder or not os.path.isdir(folder):
            self._count_hint.configure(text="")
            return
        try:
            imgs = discover_images(folder)
            n = len(imgs)
            if n > 0:
                first = load_oriented_image(imgs[0], rotation=self._rotate_var.get())
                w, h = first.size
                self._count_hint.configure(text=f"{n} image{'s' if n != 1 else ''} ({w}×{h})")
            else:
                self._count_hint.configure(text="0 images found")
        except Exception:
            self._count_hint.configure(text="")

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder", parent=self)
        if folder:
            self._output_var.set(folder)

    # ───────────────────────────────────────────────────────────────
    #  PARAMETER EXTRACTION & VALIDATION
    # ───────────────────────────────────────────────────────────────

    def _get_mode_and_params(self) -> tuple[CropMode, dict]:
        mode_str = self._mode_var.get()

        if mode_str == CropMode.EXACT_PIXELS.value:
            return CropMode.EXACT_PIXELS, {
                "left":   self._params["left"].get(),
                "top":    self._params["top"].get(),
                "right":  self._params["right"].get(),
                "bottom": self._params["bottom"].get(),
            }
        elif mode_str == CropMode.ASPECT_RATIO.value:
            return CropMode.ASPECT_RATIO, {
                "ratio_w": self._params["ratio_w"].get(),
                "ratio_h": self._params["ratio_h"].get(),
                "anchor":  self._params["anchor"].get(),
            }
        else:
            return CropMode.PERCENTAGE_TRIM, {
                "top_pct":    self._params["top_pct"].get(),
                "bottom_pct": self._params["bottom_pct"].get(),
                "left_pct":   self._params["left_pct"].get(),
                "right_pct":  self._params["right_pct"].get(),
            }

    def _get_format(self) -> str:
        return FORMAT_MAP.get(self._fmt_var.get(), "same")

    def _validate(self) -> bool:
        inp = self._input_var.get().strip()
        if not inp:
            messagebox.showwarning("Missing Input",
                                   "Please select an input folder.", parent=self)
            return False
        if not os.path.isdir(inp):
            messagebox.showwarning("Invalid Input",
                                   f"Folder not found:\n{inp}", parent=self)
            return False
        try:
            imgs = discover_images(inp)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return False
        if not imgs:
            messagebox.showwarning("No Images",
                                   "No supported images found in the input folder.\n\n"
                                   "Supported: JPG, PNG, BMP, TIFF, WebP",
                                   parent=self)
            return False
        if not self._output_var.get().strip():
            messagebox.showwarning("Missing Output",
                                   "Please select an output folder.", parent=self)
            return False

        # Warn if output == input
        out = os.path.abspath(self._output_var.get().strip())
        if os.path.abspath(inp) == out:
            ok = messagebox.askyesno(
                "Overwrite Warning",
                "Output folder is the same as input!\n"
                "Existing files will be overwritten.\n\nContinue?",
                parent=self)
            if not ok:
                return False

        return True

    # ───────────────────────────────────────────────────────────────
    #  PREVIEW
    # ───────────────────────────────────────────────────────────────

    def _preview(self):
        if not self._validate():
            return
        try:
            images = discover_images(self._input_var.get().strip())
            mode, params = self._get_mode_and_params()
            rotation = self._rotate_var.get()
            original = load_oriented_image(images[0], rotation=rotation)
            cropped = crop_single(original, mode, params)
            self._open_preview_window(original, cropped,
                                      os.path.basename(images[0]))
        except Exception as e:
            messagebox.showerror("Preview Error", str(e), parent=self)

    def _open_preview_window(self, original, processed, filename):
        """Show a before / after preview in a modal-ish popup."""
        win = tk.Toplevel(self)
        win.title(f"Crop Preview — {filename}")
        win.configure(bg=COLORS["bg_primary"])
        # Size window to 80% of main screen height, with proportional width, centered
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        target_h = int(screen_h * 0.80)
        target_w = min(int(screen_w * 0.88), int(target_h * 1.35))
        pos_x = max(0, (screen_w - target_w) // 2)
        pos_y = max(0, (screen_h - target_h) // 2)

        win.geometry(f"{target_w}x{target_h}+{pos_x}+{pos_y}")
        win.minsize(680, 420)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        # ── Header ───────────────────────────────────────────────
        hdr = ttk.Frame(win, style="TFrame")
        hdr.pack(fill="x", padx=20, pady=(14, 6))
        ttk.Label(hdr, text=f"Preview:  {filename}",
                  style="Heading.TLabel").pack(side="left")

        info = (f"{original.width}×{original.height}  →  "
                f"{processed.width}×{processed.height}")
        ttk.Label(hdr, text=info, style="Secondary.TLabel").pack(side="right")

        # ── Image panels ─────────────────────────────────────────
        panels = ttk.Frame(win, style="TFrame")
        panels.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for title, img in [("Before", original), ("After", processed)]:
            col = ttk.Frame(panels, style="TFrame")
            col.pack(side="left", fill="both", expand=True, padx=(0, 10))
            ttk.Label(col, text=title, style="Subheading.TLabel").pack(
                anchor="w", pady=(0, 4))

            canvas = tk.Canvas(col, bg=COLORS["bg_secondary"],
                               highlightthickness=1,
                               highlightbackground=COLORS["border"])
            canvas.pack(fill="both", expand=True)

            # Fit to canvas on resize
            def _draw(event, c=canvas, im=img):
                cw, ch = event.width - 4, event.height - 4
                if cw < 1 or ch < 1:
                    return
                ratio = min(cw / im.width, ch / im.height, 1.0)
                sz = (max(1, int(im.width * ratio)),
                      max(1, int(im.height * ratio)))
                thumb = im.resize(sz, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(thumb)
                c.delete("all")
                c.create_image(cw // 2 + 2, ch // 2 + 2,
                               image=photo, anchor="center")
                c._photo = photo          # prevent GC

            canvas.bind("<Configure>", _draw)

        # ── Footer ───────────────────────────────────────────────
        ttk.Button(win, text="Close", style="Browse.TButton",
                   command=win.destroy).pack(pady=(0, 14))

    # ───────────────────────────────────────────────────────────────
    #  BATCH PROCESSING
    # ───────────────────────────────────────────────────────────────

    def _start_batch(self):
        if self._processing:
            return
        if not self._validate():
            return
        try:
            mode, params = self._get_mode_and_params()
        except Exception as e:
            messagebox.showerror("Invalid Settings", str(e), parent=self)
            return

        self._processing = True
        self._toggle_controls(False)
        self._status.configure(text="Starting…")
        self._pbar["value"] = 0

        fmt = self._get_format()
        quality = self._quality_var.get()
        inp = self._input_var.get().strip()
        out = self._output_var.get().strip()
        rotation = self._rotate_var.get()

        def worker():
            try:
                res = batch_crop(
                    input_dir=inp, output_dir=out,
                    mode=mode, params=params,
                    output_format=fmt, quality=quality,
                    rotation=rotation,
                    progress_callback=lambda c, t, f, s:
                        self._queue.put(("progress", c, t, f, s)),
                )
                self._queue.put(("done", res))
            except Exception as exc:
                self._queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self):
        """Main-thread queue consumer — safe for Tkinter widget updates."""
        try:
            while True:
                msg = self._queue.get_nowait()
                kind = msg[0]

                if kind == "progress":
                    _, cur, total, fname, status = msg
                    pct = (cur / total * 100) if total else 0
                    self._pbar["value"] = pct
                    self._status.configure(text=f"Cropping:  {fname}")
                    self._counter.configure(text=f"{cur} / {total}")

                elif kind == "done":
                    res = msg[1]
                    self._processing = False
                    self._toggle_controls(True)
                    self._pbar["value"] = 100

                    self._status.configure(
                        text=f"✅  Done — {res['processed']} cropped"
                             + (f",  {res['failed']} failed" if res["failed"] else ""))

                    if res["failed"]:
                        errs = "\n".join(
                            f"• {e['file']}: {e['error']}"
                            for e in res["errors"][:15])
                        messagebox.showwarning(
                            "Some Files Failed",
                            f"{res['failed']} file(s) had errors:\n\n{errs}",
                            parent=self)
                    else:
                        messagebox.showinfo(
                            "Batch Complete",
                            f"Successfully cropped {res['processed']} images!\n\n"
                            f"Output folder:\n{self._output_var.get()}",
                            parent=self)

                elif kind == "error":
                    self._processing = False
                    self._toggle_controls(True)
                    self._status.configure(text="❌  Error occurred")
                    messagebox.showerror("Batch Error", msg[1], parent=self)

        except queue.Empty:
            pass

        self.after(80, self._poll_queue)

    def _toggle_controls(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._preview_btn.configure(state=state)
        self._start_btn.configure(state=state)
