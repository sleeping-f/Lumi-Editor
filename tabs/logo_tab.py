"""
Lumi Editor — Batch Logo Insertion Tab
Overlays a logo/watermark onto every image in a folder.
Supports six placement modes, proportional scaling, and opacity.
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

from core.logo_inserter import LogoPosition, insert_logo_single, batch_insert_logo
from core.utils import discover_images
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
#  LOGO TAB
# ═══════════════════════════════════════════════════════════════════

class LogoTab(ttk.Frame):
    """Batch logo/watermark insertion tab for the Lumi Editor notebook."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)

        self._queue = queue.Queue()
        self._processing = False
        self._logo_preview_photo = None       # prevent GC

        self._build_ui()
        self._poll_queue()

    # ───────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        container = ttk.Frame(self, style="TFrame")
        container.pack(fill="both", expand=True, padx=28, pady=16)

        self._build_folders(container)
        self._spacer(container, 12)
        self._build_logo_settings(container)
        self._spacer(container, 12)
        self._build_output_settings(container)
        self._spacer(container, 18)
        self._build_actions(container)
        self._spacer(container, 10)
        self._build_progress(container)

    @staticmethod
    def _spacer(parent, height):
        ttk.Frame(parent, height=height, style="TFrame").pack(fill="x")

    # ── 1. Folder & logo file pickers ────────────────────────────

    def _build_folders(self, parent):
        lf = ttk.LabelFrame(parent, text="  Source & Destination  ")
        lf.pack(fill="x")

        inner = ttk.Frame(lf, style="Card.TFrame")
        inner.pack(fill="x", padx=4, pady=2)

        # Input folder
        r1 = ttk.Frame(inner, style="Card.TFrame")
        r1.pack(fill="x", pady=(0, 8))
        ttk.Label(r1, text="Input Folder", width=14, style="Card.TLabel").pack(side="left")
        self._input_var = tk.StringVar()
        e1 = ttk.Entry(r1, textvariable=self._input_var)
        e1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(e1, "Folder containing images that will receive the logo")
        ttk.Button(r1, text="Browse", style="Browse.TButton",
                   command=self._browse_input).pack(side="right")

        # Output folder
        r2 = ttk.Frame(inner, style="Card.TFrame")
        r2.pack(fill="x", pady=(0, 8))
        ttk.Label(r2, text="Output Folder", width=14, style="Card.TLabel").pack(side="left")
        self._output_var = tk.StringVar()
        e2 = ttk.Entry(r2, textvariable=self._output_var)
        e2.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(e2, "Images with logo will be saved here (created automatically)")
        ttk.Button(r2, text="Browse", style="Browse.TButton",
                   command=self._browse_output).pack(side="right")

        # Logo file
        r3 = ttk.Frame(inner, style="Card.TFrame")
        r3.pack(fill="x")
        ttk.Label(r3, text="Logo File", width=14, style="Card.TLabel").pack(side="left")

        self._logo_var = tk.StringVar()
        e3 = ttk.Entry(r3, textvariable=self._logo_var)
        e3.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(e3, "Path to your logo image (PNG with transparency recommended)")

        # Logo thumbnail
        self._logo_thumb = ttk.Label(r3, style="Card.TLabel")
        self._logo_thumb.pack(side="left", padx=(0, 8))

        ttk.Button(r3, text="Browse", style="Browse.TButton",
                   command=self._browse_logo).pack(side="right")

    # ── 2. Logo placement settings ───────────────────────────────

    def _build_logo_settings(self, parent):
        lf = ttk.LabelFrame(parent, text="  Logo Settings  ")
        lf.pack(fill="x")

        inner = ttk.Frame(lf, style="Card.TFrame")
        inner.pack(fill="x", padx=4, pady=2)

        # ── Row 1: Position ──────────────────────────────────────
        row1 = ttk.Frame(inner, style="Card.TFrame")
        row1.pack(fill="x", pady=(0, 10))

        ttk.Label(row1, text="Position", width=12,
                  style="Card.TLabel").pack(side="left")
        self._pos_var = tk.StringVar(value=LogoPosition.BOTTOM_RIGHT.value)
        pcb = ttk.Combobox(row1, textvariable=self._pos_var,
                           values=[p.value for p in LogoPosition],
                           state="readonly", width=16)
        pcb.pack(side="left", padx=(0, 24))
        ToolTip(pcb, "Where to place the logo on each image")

        # Image count hint
        self._count_hint = ttk.Label(row1, text="", style="CardSecondary.TLabel")
        self._count_hint.pack(side="right")

        # ── Row 2: Scale ─────────────────────────────────────────
        row2 = ttk.Frame(inner, style="Card.TFrame")
        row2.pack(fill="x", pady=(0, 10))

        ttk.Label(row2, text="Scale", width=12,
                  style="Card.TLabel").pack(side="left")
        self._scale_var = tk.IntVar(value=15)
        sc = ttk.Scale(row2, from_=1, to=80, variable=self._scale_var,
                       orient="horizontal", command=self._on_scale)
        sc.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(sc, "Logo width as a percentage of the base image width")
        self._scale_lbl = ttk.Label(row2, text="15 %", width=6,
                                    style="CardHeading.TLabel")
        self._scale_lbl.pack(side="left")

        # ── Row 3: Opacity ───────────────────────────────────────
        row3 = ttk.Frame(inner, style="Card.TFrame")
        row3.pack(fill="x", pady=(0, 10))

        ttk.Label(row3, text="Opacity", width=12,
                  style="Card.TLabel").pack(side="left")
        self._opacity_var = tk.IntVar(value=100)
        op = ttk.Scale(row3, from_=5, to=100, variable=self._opacity_var,
                       orient="horizontal", command=self._on_opacity)
        op.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(op, "Logo transparency — lower values make it more transparent")
        self._opacity_lbl = ttk.Label(row3, text="100 %", width=6,
                                      style="CardHeading.TLabel")
        self._opacity_lbl.pack(side="left")

        # ── Row 4: Padding ───────────────────────────────────────
        row4 = ttk.Frame(inner, style="Card.TFrame")
        row4.pack(fill="x")

        ttk.Label(row4, text="Padding", width=12,
                  style="Card.TLabel").pack(side="left")
        self._padding_var = tk.IntVar(value=20)
        ps = ttk.Spinbox(row4, from_=0, to=500, textvariable=self._padding_var,
                         width=8)
        ps.pack(side="left")
        ttk.Label(row4, text="px", style="CardSecondary.TLabel").pack(
            side="left", padx=(6, 0))
        ToolTip(ps, "Pixel gap between the logo and the nearest edge(s)")

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
                                      style="CardHeading.TLabel")
        self._quality_lbl.pack(side="left")

    # ── 4. Action bar ────────────────────────────────────────────

    def _build_actions(self, parent):
        bar = ttk.Frame(parent, style="TFrame")
        bar.pack(fill="x")

        self._preview_btn = ttk.Button(bar, text="👁  Preview",
                                       command=self._preview, style="TButton")
        self._preview_btn.pack(side="left")
        ToolTip(self._preview_btn, "Preview the logo placement on the first image")

        self._start_btn = ttk.Button(bar, text="🚀  Start Batch Logo",
                                     command=self._start_batch,
                                     style="Accent.TButton")
        self._start_btn.pack(side="right")
        ToolTip(self._start_btn, "Insert logo on all images in the input folder")

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

    def _on_scale(self, val):
        self._scale_lbl.configure(text=f"{int(float(val))} %")

    def _on_opacity(self, val):
        self._opacity_lbl.configure(text=f"{int(float(val))} %")

    def _on_quality(self, val):
        self._quality_lbl.configure(text=str(int(float(val))))

    def _browse_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder", parent=self)
        if folder:
            self._input_var.set(folder)
            if not self._output_var.get():
                self._output_var.set(os.path.join(folder, "with_logo"))
            try:
                n = len(discover_images(folder))
                self._count_hint.configure(text=f"{n} image{'s' if n != 1 else ''} found")
            except Exception:
                self._count_hint.configure(text="")

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder", parent=self)
        if folder:
            self._output_var.set(folder)

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"),
                ("PNG (recommended)", "*.png"),
                ("All files", "*.*"),
            ],
            parent=self,
        )
        if path:
            self._logo_var.set(path)
            self._show_logo_thumbnail(path)

    def _show_logo_thumbnail(self, path):
        """Display a small thumbnail of the selected logo."""
        try:
            logo = Image.open(path)
            # Fit into 32×32
            logo.thumbnail((32, 32), Image.Resampling.LANCZOS)
            self._logo_preview_photo = ImageTk.PhotoImage(logo)
            self._logo_thumb.configure(image=self._logo_preview_photo)
        except Exception:
            self._logo_thumb.configure(image="")

    # ───────────────────────────────────────────────────────────────
    #  PARAMETER EXTRACTION & VALIDATION
    # ───────────────────────────────────────────────────────────────

    def _get_position(self) -> LogoPosition:
        val = self._pos_var.get()
        for p in LogoPosition:
            if p.value == val:
                return p
        return LogoPosition.BOTTOM_RIGHT

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
                                   "No supported images found.\n\n"
                                   "Supported: JPG, PNG, BMP, TIFF, WebP",
                                   parent=self)
            return False

        logo = self._logo_var.get().strip()
        if not logo:
            messagebox.showwarning("Missing Logo",
                                   "Please select a logo file.", parent=self)
            return False
        if not os.path.isfile(logo):
            messagebox.showwarning("Invalid Logo",
                                   f"Logo file not found:\n{logo}", parent=self)
            return False

        if not self._output_var.get().strip():
            messagebox.showwarning("Missing Output",
                                   "Please select an output folder.", parent=self)
            return False

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
            logo = Image.open(self._logo_var.get().strip())
            original = Image.open(images[0])

            position  = self._get_position()
            scale_pct = self._scale_var.get()
            opacity   = self._opacity_var.get() / 100.0
            padding   = self._padding_var.get()

            result = insert_logo_single(
                original, logo, position, scale_pct, opacity, padding)

            self._open_preview_window(original, result,
                                      os.path.basename(images[0]))
        except Exception as e:
            messagebox.showerror("Preview Error", str(e), parent=self)

    def _open_preview_window(self, original, processed, filename):
        """Show before / after preview in a popup."""
        win = tk.Toplevel(self)
        win.title(f"Logo Preview — {filename}")
        win.configure(bg=COLORS["bg_primary"])
        win.geometry("960x540")
        win.minsize(600, 350)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        # Header
        hdr = ttk.Frame(win, style="TFrame")
        hdr.pack(fill="x", padx=20, pady=(14, 6))
        ttk.Label(hdr, text=f"Preview:  {filename}",
                  style="Heading.TLabel").pack(side="left")
        info = f"{original.width}×{original.height}"
        ttk.Label(hdr, text=info, style="Secondary.TLabel").pack(side="right")

        # Image panels
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
                c._photo = photo

            canvas.bind("<Configure>", _draw)

        # Footer
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

        self._processing = True
        self._toggle_controls(False)
        self._status.configure(text="Starting…")
        self._pbar["value"] = 0

        position   = self._get_position()
        scale_pct  = self._scale_var.get()
        opacity    = self._opacity_var.get() / 100.0
        padding    = self._padding_var.get()
        fmt        = self._get_format()
        quality    = self._quality_var.get()
        inp        = self._input_var.get().strip()
        out        = self._output_var.get().strip()
        logo_path  = self._logo_var.get().strip()

        def worker():
            try:
                res = batch_insert_logo(
                    input_dir=inp, output_dir=out,
                    logo_path=logo_path, position=position,
                    scale_pct=scale_pct, opacity=opacity,
                    padding=padding, output_format=fmt, quality=quality,
                    progress_callback=lambda c, t, f, s:
                        self._queue.put(("progress", c, t, f, s)),
                )
                self._queue.put(("done", res))
            except Exception as exc:
                self._queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self):
        try:
            while True:
                msg = self._queue.get_nowait()
                kind = msg[0]

                if kind == "progress":
                    _, cur, total, fname, status = msg
                    pct = (cur / total * 100) if total else 0
                    self._pbar["value"] = pct
                    self._status.configure(text=f"Adding logo:  {fname}")
                    self._counter.configure(text=f"{cur} / {total}")

                elif kind == "done":
                    res = msg[1]
                    self._processing = False
                    self._toggle_controls(True)
                    self._pbar["value"] = 100

                    self._status.configure(
                        text=f"✅  Done — {res['processed']} processed"
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
                            f"Logo inserted on {res['processed']} images!\n\n"
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
