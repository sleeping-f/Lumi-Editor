"""
Lumi Editor — Batch Image Editing Tool
Entry point and main application window.

    python main.py

Requires:  pip install Pillow
"""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from theme import COLORS, FONTS, apply_theme
from tabs.crop_tab import CropTab
from tabs.logo_tab import LogoTab


# ── DPI awareness (Windows) ─────────────────────────────────────
# Must be called before any Tk window is created.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ═══════════════════════════════════════════════════════════════════
#  APPLICATION CLASS
# ═══════════════════════════════════════════════════════════════════

class LumiEditorApp:
    """Main application: branded header + tabbed content area."""

    # Window defaults
    WIN_TITLE    = "Lumi Editor"
    WIN_SIZE     = "980x720"
    WIN_MIN      = (780, 560)

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.WIN_TITLE)
        self.root.geometry(self.WIN_SIZE)
        self.root.minsize(*self.WIN_MIN)

        # Apply the custom theme
        apply_theme(self.root)

        # Set the window icon
        self._set_icon()

        # Build the UI
        self._build_header()
        self._build_tabs()
        self._build_footer()

    # ───────────────────────────────────────────────────────────────
    #  WINDOW ICON
    # ───────────────────────────────────────────────────────────────

    def _set_icon(self):
        """Set the taskbar and title-bar icon from the logo asset."""
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if not os.path.isfile(logo_path):
            return
        try:
            icon = Image.open(logo_path)
            self._icon_photo = ImageTk.PhotoImage(icon)
            self.root.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    # ───────────────────────────────────────────────────────────────
    #  HEADER  (dark banner with logo + branding)
    # ───────────────────────────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["bg_dark"], height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Logo thumbnail
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.isfile(logo_path):
            try:
                logo = Image.open(logo_path)
                logo.thumbnail((40, 40), Image.Resampling.LANCZOS)
                self._header_logo = ImageTk.PhotoImage(logo)
                tk.Label(header, image=self._header_logo,
                         bg=COLORS["bg_dark"]).pack(
                    side="left", padx=(20, 12), pady=10)
            except Exception:
                pass

        # Title
        tk.Label(
            header, text="Lumi Editor",
            font=FONTS["title"],
            fg=COLORS["text_on_dark"],
            bg=COLORS["bg_dark"],
        ).pack(side="left", pady=(10, 10))

        # Tagline
        tk.Label(
            header, text="Batch Edit. Simplified.",
            font=FONTS["tagline"],
            fg=COLORS["accent"],
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(10, 0), pady=(12, 10))

        # Gold accent line under header
        accent_bar = tk.Frame(self.root, bg=COLORS["accent"], height=3)
        accent_bar.pack(fill="x", side="top")

    # ───────────────────────────────────────────────────────────────
    #  TABBED CONTENT AREA
    # ───────────────────────────────────────────────────────────────

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Tab 1: Batch Crop ────────────────────────────────────
        self.crop_tab = CropTab(self.notebook)
        self.notebook.add(self.crop_tab, text="  ✂  Batch Crop  ")

        # ── Tab 2: Batch Logo ────────────────────────────────────
        self.logo_tab = LogoTab(self.notebook)
        self.notebook.add(self.logo_tab, text="  🖼  Batch Logo  ")

    # ───────────────────────────────────────────────────────────────
    #  FOOTER
    # ───────────────────────────────────────────────────────────────

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["bg_hover"], height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="Lumi Editor  •  Batch Edit. Simplified.  •  Powered by Pillow",
            font=("Segoe UI", 8),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_hover"],
        ).pack(side="left", padx=16, pady=6)

        tk.Label(
            footer,
            text="v1.0",
            font=("Segoe UI", 8),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_hover"],
        ).pack(side="right", padx=16, pady=6)

    # ───────────────────────────────────────────────────────────────
    #  RUN
    # ───────────────────────────────────────────────────────────────

    def run(self):
        """Enter the Tk main loop."""
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    app = LumiEditorApp()
    app.run()


if __name__ == "__main__":
    main()
