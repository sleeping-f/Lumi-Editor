"""
Lumi Editor — Custom Theme & Styling
Visual identity derived from the Lumi Editor brand:
dark charcoal base · warm gold accent · clean modern layout.
"""

import tkinter as tk
from tkinter import ttk


# ═══════════════════════════════════════════════════════════════════
#  COLOR PALETTES (DARK & LIGHT)
# ═══════════════════════════════════════════════════════════════════

DARK_COLORS = {
    # ── Backgrounds ──────────────────────────────────────────────
    "bg_primary":     "#121218",      # main window background (deep obsidian)
    "bg_secondary":   "#1b1b26",      # cards / panels (elevated charcoal)
    "bg_navbar":      "#151520",      # top navigation bar (sleek dark)
    "bg_dark":        "#151520",      # header
    "bg_darker":      "#0e0e16",      # deeper contrast
    "bg_input":       "#171724",      # entry / spinbox field background
    "bg_hover":       "#262638",      # hover state on dark surfaces

    # ── Accent (warm luminous gold from brand) ───────────────────
    "accent":         "#d4af37",      # radiant gold
    "accent_hover":   "#e2bc52",      # brighter gold on hover
    "accent_light":   "#2a2414",      # subtle dark gold tint
    "accent_subtle":  "#221d10",      # very subtle dark gold
    "accent_bar":     "#d4af37",      # divider under navbar

    # ── Text ─────────────────────────────────────────────────────
    "text_primary":   "#f3f3f8",      # high contrast crisp text
    "text_secondary": "#a2a2b8",      # comfortable secondary text
    "text_muted":     "#6f6f86",      # hints, captions
    "text_disabled":  "#4a4a62",      # disabled controls
    "text_on_dark":   "#f3f3f8",      # text on navbar
    "text_on_accent": "#121218",      # text on gold buttons

    # ── Borders ──────────────────────────────────────────────────
    "border":         "#2d2d3e",      # clean hairline borders
    "border_focus":   "#d4af37",      # radiant gold focus ring

    # ── Status ───────────────────────────────────────────────────
    "success":        "#4ade80",      # modern emerald green
    "success_bg":     "#12281a",      # dark green tint
    "error":          "#f87171",      # modern coral red
    "error_bg":       "#2d1416",      # dark red tint

    # ── Progress bar ─────────────────────────────────────────────
    "progress_bg":    "#242436",
    "progress_fill":  "#d4af37",

    # ── Tabs ─────────────────────────────────────────────────────
    "tab_bg":         "#171724",      # inactive tabs
    "tab_selected":   "#1b1b26",      # active tab matches card surface
    "tab_hover":      "#242436",      # tab hover
}

LIGHT_COLORS = {
    # ── Backgrounds ──────────────────────────────────────────────
    "bg_primary":     "#f5f5f9",      # main window
    "bg_secondary":   "#ffffff",      # cards / panels
    "bg_navbar":      "#ffffff",      # navbar background (EXACT LOGO WHITE so it blends!)
    "bg_dark":        "#ffffff",      # header is white
    "bg_darker":      "#f0f0f5",      # subtle light contrast
    "bg_input":       "#ffffff",      # input fields
    "bg_hover":       "#eaeaf2",      # hover state

    # ── Accent (warm gold from logo) ─────────────────────────────
    "accent":         "#c9a84c",      # warm gold
    "accent_hover":   "#b89840",      # deeper gold on hover
    "accent_light":   "#f7f0dc",      # soft champagne tint
    "accent_subtle":  "#fbf7ed",      # subtle warm tint
    "accent_bar":     "#c9a84c",      # 2px divider under navbar

    # ── Text ─────────────────────────────────────────────────────
    "text_primary":   "#1e1e2e",      # dark charcoal primary text
    "text_secondary": "#5a5a72",      # readable secondary text
    "text_muted":     "#8c8ca0",      # hints / captions
    "text_disabled":  "#b4b4c4",      # disabled text
    "text_on_dark":   "#1e1e2e",      # dark text on white navbar
    "text_on_accent": "#1e1e2e",

    # ── Borders ──────────────────────────────────────────────────
    "border":         "#e2e2ec",      # soft subtle border
    "border_focus":   "#c9a84c",      # gold focus ring

    # ── Status ───────────────────────────────────────────────────
    "success":        "#2e7d32",
    "success_bg":     "#e8f5e9",
    "error":          "#c62828",
    "error_bg":       "#ffebee",

    # ── Progress bar ─────────────────────────────────────────────
    "progress_bg":    "#e2e2ec",
    "progress_fill":  "#c9a84c",

    # ── Tabs ─────────────────────────────────────────────────────
    "tab_bg":         "#eaeaf2",
    "tab_selected":   "#ffffff",
    "tab_hover":      "#dedee8",
}

CURRENT_THEME = "dark"
COLORS = dict(DARK_COLORS)


def get_theme_mode() -> str:
    """Return active theme mode: 'dark' or 'light'."""
    return CURRENT_THEME


def set_theme_mode(mode: str) -> None:
    """Set active theme dictionary and state."""
    global CURRENT_THEME
    CURRENT_THEME = "light" if mode == "light" else "dark"
    if CURRENT_THEME == "light":
        COLORS.clear()
        COLORS.update(LIGHT_COLORS)
    else:
        COLORS.clear()
        COLORS.update(DARK_COLORS)


def toggle_theme(root: tk.Tk) -> str:
    """Toggle between dark and light mode, reapplying styles."""
    new_mode = "light" if CURRENT_THEME == "dark" else "dark"
    set_theme_mode(new_mode)
    apply_theme(root, mode=new_mode)
    return new_mode


# ═══════════════════════════════════════════════════════════════════
#  FONT STACK  (Segoe UI — native Windows; falls back gracefully)
# ═══════════════════════════════════════════════════════════════════

FONTS = {
    "title":        ("Segoe UI", 16, "bold"),
    "heading":      ("Segoe UI", 13, "bold"),
    "subheading":   ("Segoe UI", 10, "bold"),
    "body":         ("Segoe UI", 10),
    "body_small":   ("Segoe UI", 9),
    "button":       ("Segoe UI", 10, "bold"),
    "button_small": ("Segoe UI", 9),
    "input":        ("Segoe UI", 10),
    "status":       ("Segoe UI", 9),
    "tab":          ("Segoe UI", 10, "bold"),
    "tagline":      ("Segoe UI", 10),
}


# ═══════════════════════════════════════════════════════════════════
#  THEME APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_theme(root: tk.Tk, mode: str = None) -> ttk.Style:
    """
    Apply the Lumi Editor theme (Dark Mode by default).
    Call this once on init, or whenever toggling theme mode.
    """
    if mode is not None:
        set_theme_mode(mode)

    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=COLORS["bg_primary"])

    # Configure combobox dropdown listbox colors
    root.option_add("*TCombobox*Listbox.background", COLORS["bg_input"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text_primary"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["text_on_accent"])

    # ── Frames ───────────────────────────────────────────────────
    style.configure("TFrame", background=COLORS["bg_primary"])
    style.configure("Card.TFrame", background=COLORS["bg_secondary"])
    style.configure("Dark.TFrame", background=COLORS["bg_dark"])

    # ── Labels ───────────────────────────────────────────────────
    _lbl = dict(background=COLORS["bg_primary"], foreground=COLORS["text_primary"])

    style.configure("TLabel", font=FONTS["body"], **_lbl)
    style.configure("Heading.TLabel",    font=FONTS["heading"],    **_lbl)
    style.configure("Subheading.TLabel", font=FONTS["subheading"], **_lbl)
    style.configure("Secondary.TLabel",  font=FONTS["body_small"],
                    background=COLORS["bg_primary"],
                    foreground=COLORS["text_secondary"])
    style.configure("Status.TLabel",     font=FONTS["status"],
                    background=COLORS["bg_primary"],
                    foreground=COLORS["text_secondary"])
    style.configure("Success.TLabel",    font=FONTS["body"],
                    background=COLORS["bg_primary"],
                    foreground=COLORS["success"])
    style.configure("Error.TLabel",      font=FONTS["body"],
                    background=COLORS["bg_primary"],
                    foreground=COLORS["error"])

    # Card labels (secondary bg)
    style.configure("Card.TLabel",
                    font=FONTS["body"],
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["text_primary"])
    style.configure("CardHeading.TLabel",
                    font=FONTS["subheading"],
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["text_primary"])
    style.configure("CardSecondary.TLabel",
                    font=FONTS["body_small"],
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["text_secondary"])

    # ── Buttons ──────────────────────────────────────────────────
    style.configure("TButton",
                    font=FONTS["button"], padding=(16, 8),
                    background=COLORS["bg_hover"],
                    foreground=COLORS["text_primary"],
                    borderwidth=0, focuscolor="none")
    style.map("TButton",
              background=[("active",   COLORS["accent"]),
                          ("pressed",  COLORS["accent_hover"]),
                          ("disabled", COLORS["bg_primary"])],
              foreground=[("active",   COLORS["text_on_accent"]),
                          ("pressed",  COLORS["text_on_accent"]),
                          ("disabled", COLORS["text_disabled"])])

    # Primary / accent
    style.configure("Accent.TButton",
                    font=FONTS["button"], padding=(22, 10),
                    background=COLORS["accent"],
                    foreground=COLORS["text_on_accent"],
                    borderwidth=0, focuscolor="none")
    style.map("Accent.TButton",
              background=[("active",   COLORS["accent_hover"]),
                          ("pressed",  COLORS["accent"]),
                          ("disabled", COLORS["bg_hover"])],
              foreground=[("active",   COLORS["text_on_accent"]),
                          ("pressed",  COLORS["text_on_accent"]),
                          ("disabled", COLORS["text_disabled"])])

    # Browse (small, neutral)
    style.configure("Browse.TButton",
                    font=FONTS["button_small"], padding=(12, 6),
                    background=COLORS["bg_hover"],
                    foreground=COLORS["text_primary"],
                    borderwidth=0, focuscolor="none")
    style.map("Browse.TButton",
              background=[("active",  COLORS["border"]),
                          ("pressed", COLORS["accent_light"])],
              foreground=[("disabled", COLORS["text_disabled"])])

    # ── Entries ──────────────────────────────────────────────────
    style.configure("TEntry",
                    font=FONTS["input"], padding=(8, 6),
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    borderwidth=1,
                    bordercolor=COLORS["border"],
                    lightcolor=COLORS["border"],
                    darkcolor=COLORS["border"])
    style.map("TEntry",
              bordercolor=[("focus", COLORS["border_focus"])],
              lightcolor=[("focus",  COLORS["border_focus"])],
              darkcolor=[("focus",   COLORS["border_focus"])])

    # ── Combobox ─────────────────────────────────────────────────
    style.configure("TCombobox",
                    font=FONTS["input"], padding=(8, 6),
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    background=COLORS["bg_secondary"],
                    darkcolor=COLORS["border"],
                    lightcolor=COLORS["border"],
                    bordercolor=COLORS["border"],
                    borderwidth=1, arrowsize=14)
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["bg_input"])],
              bordercolor=[("focus", COLORS["border_focus"])])

    # ── Spinbox ──────────────────────────────────────────────────
    style.configure("TSpinbox",
                    font=FONTS["input"], padding=(8, 6),
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    background=COLORS["bg_secondary"],
                    darkcolor=COLORS["border"],
                    lightcolor=COLORS["border"],
                    bordercolor=COLORS["border"],
                    borderwidth=1, arrowsize=14)
    style.map("TSpinbox",
              bordercolor=[("focus", COLORS["border_focus"])])

    # ── Scale (slider) ───────────────────────────────────────────
    style.configure("Horizontal.TScale",
                    background=COLORS["bg_secondary"],
                    troughcolor=COLORS["progress_bg"],
                    sliderthickness=16, borderwidth=0)

    # ── Progressbar ──────────────────────────────────────────────
    style.configure("Horizontal.TProgressbar",
                    background=COLORS["progress_fill"],
                    troughcolor=COLORS["progress_bg"],
                    borderwidth=0, thickness=6)

    style.configure("Gold.Horizontal.TProgressbar",
                    background=COLORS["accent"],
                    troughcolor=COLORS["progress_bg"],
                    borderwidth=0, thickness=6)

    # ── Notebook (tabs) ──────────────────────────────────────────
    style.configure("TNotebook",
                    background=COLORS["bg_primary"],
                    borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab",
                    font=FONTS["tab"], padding=(28, 10),
                    background=COLORS["tab_bg"],
                    foreground=COLORS["text_secondary"],
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["tab_selected"]),
                          ("active",   COLORS["tab_hover"])],
              foreground=[("selected", COLORS["accent"]),
                          ("active",   COLORS["text_primary"])],
              expand=[("selected", [0, 0, 0, 2])])

    # ── LabelFrame ───────────────────────────────────────────────
    style.configure("TLabelframe",
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["text_primary"],
                    borderwidth=1, relief="solid",
                    bordercolor=COLORS["border"],
                    padding=(14, 10))
    style.configure("TLabelframe.Label",
                    font=FONTS["subheading"],
                    foreground=COLORS["accent"],
                    background=COLORS["bg_secondary"])

    # ── Separator ────────────────────────────────────────────────
    style.configure("TSeparator", background=COLORS["border"])

    return style


# ═══════════════════════════════════════════════════════════════════
#  TOOLTIP WIDGET
# ═══════════════════════════════════════════════════════════════════

class ToolTip:
    """
    Hover tooltip that appears after a short delay.
    Styled to match the Lumi dark palette.
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget   = widget
        self.text     = text
        self.delay    = delay
        self._tip_win = None
        self._after   = None

        widget.bind("<Enter>",       self._schedule)
        widget.bind("<Leave>",       self._cancel)
        widget.bind("<ButtonPress>", self._cancel)

    # ── internal ─────────────────────────────────────────────────

    def _schedule(self, _event=None):
        self._cancel()
        self._after = self.widget.after(self.delay, self._show)

    def _cancel(self, _event=None):
        if self._after:
            self.widget.after_cancel(self._after)
            self._after = None
        self._hide()

    def _show(self):
        if self._tip_win:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        frame = tk.Frame(tw, bg=COLORS["bg_dark"], padx=10, pady=6)
        frame.pack()

        tk.Label(
            frame, text=self.text,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_on_dark"],
            font=("Segoe UI", 9),
            wraplength=320, justify="left",
        ).pack()

        self._tip_win = tw

    def _hide(self):
        if self._tip_win:
            self._tip_win.destroy()
            self._tip_win = None
