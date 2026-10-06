"""
Lumi Editor — Custom Theme & Styling
Visual identity derived from the Lumi Editor brand:
dark charcoal base · warm gold accent · clean modern layout.
"""

import tkinter as tk
from tkinter import ttk


# ═══════════════════════════════════════════════════════════════════
#  COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    # ── Backgrounds ──────────────────────────────────────────────
    "bg_primary":     "#f4f4f8",      # main window
    "bg_secondary":   "#ffffff",      # cards / panels
    "bg_dark":        "#2d2d3f",      # header, dark buttons
    "bg_darker":      "#1e1e2e",      # deeper dark
    "bg_input":       "#ffffff",      # input fields
    "bg_hover":       "#eaeaf0",      # hover state

    # ── Accent (warm gold from logo) ─────────────────────────────
    "accent":         "#c9a84c",
    "accent_hover":   "#b89840",
    "accent_light":   "#f5ecd4",
    "accent_subtle":  "#ede3c8",

    # ── Text ─────────────────────────────────────────────────────
    "text_primary":   "#2d2d3f",
    "text_secondary": "#6b6b80",
    "text_muted":     "#9e9eb0",
    "text_disabled":  "#b8b8c8",
    "text_on_dark":   "#f0f0f5",
    "text_on_accent": "#2d2d3f",

    # ── Borders ──────────────────────────────────────────────────
    "border":         "#e0e0e8",
    "border_focus":   "#c9a84c",

    # ── Status ───────────────────────────────────────────────────
    "success":        "#4caf50",
    "success_bg":     "#e8f5e9",
    "error":          "#ef5350",
    "error_bg":       "#ffebee",

    # ── Progress bar ─────────────────────────────────────────────
    "progress_bg":    "#e0e0e8",
    "progress_fill":  "#c9a84c",

    # ── Tabs ─────────────────────────────────────────────────────
    "tab_bg":         "#eaeaf0",
    "tab_selected":   "#ffffff",
    "tab_hover":      "#d8d8e2",
}

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

def apply_theme(root: tk.Tk) -> ttk.Style:
    """
    Apply the Lumi Editor custom theme on top of the 'clam' base.
    Call this once, immediately after creating the root window.

    Returns:
        The configured ttk.Style instance.
    """
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=COLORS["bg_primary"])

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

    # Card labels (white bg)
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

    # Default (dark charcoal)
    style.configure("TButton",
                    font=FONTS["button"], padding=(16, 8),
                    background=COLORS["bg_dark"],
                    foreground=COLORS["text_on_dark"],
                    borderwidth=0, focuscolor="none")
    style.map("TButton",
              background=[("active",   COLORS["accent"]),
                          ("pressed",  COLORS["accent_hover"]),
                          ("disabled", COLORS["bg_hover"])],
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
                          ("pressed",  COLORS["bg_dark"]),
                          ("disabled", COLORS["bg_hover"])],
              foreground=[("active",   COLORS["text_on_accent"]),
                          ("pressed",  COLORS["text_on_dark"]),
                          ("disabled", COLORS["text_disabled"])])

    # Browse (small, neutral)
    style.configure("Browse.TButton",
                    font=FONTS["button_small"], padding=(12, 6),
                    background=COLORS["bg_hover"],
                    foreground=COLORS["text_primary"],
                    borderwidth=0, focuscolor="none")
    style.map("Browse.TButton",
              background=[("active",  COLORS["border"]),
                          ("pressed", COLORS["accent_light"])])

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
                    borderwidth=1, arrowsize=14)
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["bg_input"])],
              bordercolor=[("focus", COLORS["border_focus"])])

    # ── Spinbox ──────────────────────────────────────────────────
    style.configure("TSpinbox",
                    font=FONTS["input"], padding=(8, 6),
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
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
              foreground=[("selected", COLORS["text_primary"]),
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
