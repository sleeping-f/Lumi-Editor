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


from theme import COLORS, FONTS, apply_theme, get_theme_mode, toggle_theme, ToolTip
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

    def _get_header_logo(self) -> ImageTk.PhotoImage:
        """
        Load the 25% bigger (50x50) logo and alpha-composite directly onto the
        exact navbar background color for 100% seamless blending without edge boxes.
        """
        mode = get_theme_mode()
        asset_name = "logo_navbar_dark.png" if mode == "dark" else "logo_navbar_light.png"
        logo_path = resource_path(os.path.join("assets", asset_name))
        if not os.path.isfile(logo_path):
            logo_path = resource_path(os.path.join("assets", "logo.png"))

        try:
            img = Image.open(logo_path).convert("RGBA")
            img = img.resize((50, 50), Image.Resampling.LANCZOS)

            bg_hex = COLORS["bg_navbar"]
            bg_canvas = Image.new("RGBA", (50, 50), bg_hex)
            bg_canvas.alpha_composite(img)
            return ImageTk.PhotoImage(bg_canvas)
        except Exception:
            fallback = Image.new("RGBA", (50, 50), COLORS["bg_navbar"])
            return ImageTk.PhotoImage(fallback)

    def _build_header(self):
        # Header banner (spacious height 68 to comfortably frame the 50x50 logo)
        header = tk.Frame(self.root, bg=COLORS["bg_navbar"], height=68)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        self._header_frame = header

        # 25% Bigger Logo (50x50), blended seamlessly into navbar
        self._header_logo = self._get_header_logo()
        self._logo_label = tk.Label(
            header,
            image=self._header_logo,
            bg=COLORS["bg_navbar"]
        )
        self._logo_label.pack(side="left", padx=(20, 14), pady=9)

        # Title
        self._title_label = tk.Label(
            header, text="Lumi Editor",
            font=FONTS["title"],
            fg=COLORS["text_on_dark"],
            bg=COLORS["bg_navbar"],
        )
        self._title_label.pack(side="left", pady=(14, 14))

        # Tagline
        self._tagline_label = tk.Label(
            header, text="Batch Edit. Simplified.",
            font=FONTS["tagline"],
            fg=COLORS["accent"],
            bg=COLORS["bg_navbar"],
        )
        self._tagline_label.pack(side="left", padx=(10, 0), pady=(16, 14))

        # Right side controls: Check Updates + Theme Toggle
        btn_container = tk.Frame(header, bg=COLORS["bg_navbar"])
        btn_container.pack(side="right", padx=16, pady=14)
        self._header_btn_container = btn_container

        # 1. Update button
        self._update_btn = tk.Button(
            btn_container,
            text="✨ Check Updates",
            font=FONTS["button_small"],
            bg=COLORS["bg_hover"],
            fg=COLORS["accent"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["text_on_accent"],
            relief="flat",
            padx=12, pady=5,
            cursor="hand2",
            command=self._open_updater
        )
        self._update_btn.pack(side="right")
        ToolTip(self._update_btn, "Check for new versions and software updates")

        # 2. Theme Toggle button (Dark by default -> shows option to switch to Light)
        initial_theme_text = "☀️  Light" if get_theme_mode() == "dark" else "🌙  Dark"
        self._theme_btn = tk.Button(
            btn_container,
            text=initial_theme_text,
            font=FONTS["button_small"],
            bg=COLORS["bg_hover"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["text_on_accent"],
            relief="flat",
            padx=12, pady=5,
            cursor="hand2",
            command=self._toggle_theme
        )
        self._theme_btn.pack(side="right", padx=(0, 10))
        ToolTip(self._theme_btn, "Toggle between Dark and Light mode")

        # Signature accent bar under header
        self._accent_bar = tk.Frame(self.root, bg=COLORS["accent_bar"], height=2)
        self._accent_bar.pack(fill="x", side="top")

    def _toggle_theme(self):
        """Toggle application between dark and light themes smoothly."""
        new_mode = toggle_theme(self.root)

        # Update header
        self._header_frame.configure(bg=COLORS["bg_navbar"])
        self._header_btn_container.configure(bg=COLORS["bg_navbar"])

        self._header_logo = self._get_header_logo()
        self._logo_label.configure(image=self._header_logo, bg=COLORS["bg_navbar"])
        self._title_label.configure(fg=COLORS["text_on_dark"], bg=COLORS["bg_navbar"])
        self._tagline_label.configure(fg=COLORS["accent"], bg=COLORS["bg_navbar"])

        theme_text = "☀️  Light" if new_mode == "dark" else "🌙  Dark"
        self._theme_btn.configure(
            text=theme_text,
            bg=COLORS["bg_hover"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["text_on_accent"]
        )
        self._update_btn.configure(
            bg=COLORS["bg_hover"],
            fg=COLORS["accent"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["text_on_accent"]
        )
        self._accent_bar.configure(bg=COLORS["accent_bar"])

        # Update footer
        self._footer.configure(bg=COLORS["bg_hover"])
        self._footer_credits.configure(bg=COLORS["bg_hover"], fg=COLORS["text_muted"])
        self._footer_version.configure(bg=COLORS["bg_hover"], fg=COLORS["accent"])

        # Update tabs canvases
        if hasattr(self, "crop_tab"):
            self.crop_tab.update_theme()
        if hasattr(self, "logo_tab"):
            self.logo_tab.update_theme()

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
        self._footer = footer

        self._footer_credits = tk.Label(
            footer,
            text="Lumi Editor  •  Developed by Md. Farhan Sadique  •  Batch Edit. Simplified.",
            font=("Segoe UI", 8),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_hover"],
        )
        self._footer_credits.pack(side="left", padx=16, pady=6)

        self._footer_version = tk.Label(
            footer,
            text=f"v{CURRENT_VERSION}",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["bg_hover"],
            cursor="hand2",
        )
        self._footer_version.pack(side="right", padx=16, pady=6)
        self._footer_version.bind("<Button-1>", lambda e: self._open_updater())
        ToolTip(self._footer_version, "Click to check for updates")

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
