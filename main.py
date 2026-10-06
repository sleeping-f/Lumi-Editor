"""
Lumi Editor — Batch Image Editing Tool
Developed by Md. Farhan Sadique

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


# ── PyInstaller bundle support ──────────────────────────────────
# When running as a bundled .exe, assets live under sys._MEIPASS.
# In dev mode, they live next to this script.

def resource_path(relative_path: str) -> str:
    """Resolve a path to a bundled resource (works in both dev and .exe)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


# ── DPI awareness (Windows) ─────────────────────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


from theme import COLORS, FONTS, apply_theme, ToolTip
from tabs.crop_tab import CropTab
from tabs.logo_tab import LogoTab
from core.updater import CURRENT_VERSION, UpdateDialog


# ═══════════════════════════════════════════════════════════════════
#  APPLICATION CLASS
# ═══════════════════════════════════════════════════════════════════

class LumiEditorApp:
    """Main application: branded header + tabbed content area."""

    # Window defaults
    WIN_TITLE = "Lumi Editor"
    WIN_MIN   = (840, 580)

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.WIN_TITLE)
        self.root.minsize(*self.WIN_MIN)

        # Apply the custom theme
        apply_theme(self.root)

        # Set the window icon
        self._set_icon()

        # Build the UI
        self._build_header()
        self._build_tabs()
        self._build_footer()

        # Set optimal geometry so all controls & progress bar are immediately visible
        self._apply_ideal_geometry()

    def _apply_ideal_geometry(self):
        """Size and center window ideally based on screen resolution and content requirements."""
        self.root.update_idletasks()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        req_w = self.root.winfo_reqwidth()
        req_h = self.root.winfo_reqheight()

        # Target width has comfortable horizontal breathing room (default 1020px)
        target_w = max(1020, min(req_w + 60, screen_w - 60))
        target_w = min(target_w, screen_w - 40)

        # Target height fits all content, action buttons, and progress bar with generous margin
        target_h = max(880, min(req_h + 30, screen_h - 70))
        target_h = min(target_h, screen_h - 70)

        pos_x = max(0, (screen_w - target_w) // 2)
        pos_y = max(0, (screen_h - target_h) // 2)

        self.root.geometry(f"{target_w}x{target_h}+{pos_x}+{pos_y}")

    # ───────────────────────────────────────────────────────────────
    #  WINDOW ICON
    # ───────────────────────────────────────────────────────────────

    def _set_icon(self):
        """Set the taskbar and title-bar icon from the logo asset."""
        logo_path = resource_path(os.path.join("assets", "logo.png"))
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
        logo_path = resource_path(os.path.join("assets", "logo.png"))
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

        # Right side: Update button in header
        update_btn = tk.Button(
            header,
            text="✨ Check Updates",
            font=FONTS["button_small"],
            bg=COLORS["bg_darker"],
            fg=COLORS["accent"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["bg_darker"],
            relief="flat",
            padx=10, pady=4,
            cursor="hand2",
            command=self._open_updater
        )
        update_btn.pack(side="right", padx=16, pady=12)
        ToolTip(update_btn, "Check for new versions and software updates")

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
            text="Lumi Editor  •  Developed by Md. Farhan Sadique  •  Batch Edit. Simplified.",
            font=("Segoe UI", 8),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_hover"],
        ).pack(side="left", padx=16, pady=6)

        ver_lbl = tk.Label(
            footer,
            text=f"v{CURRENT_VERSION}",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["bg_hover"],
            cursor="hand2",
        )
        ver_lbl.pack(side="right", padx=16, pady=6)
        ver_lbl.bind("<Button-1>", lambda e: self._open_updater())
        ToolTip(ver_lbl, "Click to check for updates")

    def _open_updater(self):
        """Open the update manager dialog."""
        UpdateDialog(self.root)

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
