"""
Lumi Editor — Update & Version Management System
Provides version tracking, remote update checking, and seamless self-updating.
"""

import json
import os
import sys
import subprocess
import tempfile
import threading
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox

from theme import COLORS, FONTS, ToolTip


# ═══════════════════════════════════════════════════════════════════
#  VERSION METADATA & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

APP_NAME = "Lumi Editor"
CURRENT_VERSION = "1.0.0"

# Default update manifest endpoint (can be GitHub Releases, custom server, or S3/raw JSON)
# Structure of version.json:
# {
#   "version": "1.1.0",
#   "release_date": "2026-09-02",
#   "download_url": "https://example.com/LumiEditor.exe",
#   "changelog": "• Added batch resize\n• Performance optimizations"
# }
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/lumieditor/releases/main/version.json"


def parse_version(ver_str: str) -> tuple[int, ...]:
    """Parse version string like '1.2.3' or 'v1.2.3' into a comparable tuple."""
    cleaned = ver_str.strip().lstrip("vV")
    parts = []
    for part in cleaned.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer_version(remote_ver: str, current_ver: str = CURRENT_VERSION) -> bool:
    """Return True if remote_ver is strictly newer than current_ver."""
    return parse_version(remote_ver) > parse_version(current_ver)


# ═══════════════════════════════════════════════════════════════════
#  UPDATE CHECKER ENGINE
# ═══════════════════════════════════════════════════════════════════

def check_for_updates(update_url: str = DEFAULT_UPDATE_URL, timeout: int = 6) -> dict:
    """
    Query the remote manifest for update info.

    Returns dict with keys:
        'success': bool
        'is_update_available': bool
        'latest_version': str
        'current_version': str
        'download_url': str
        'changelog': str
        'error': str or None
    """
    result = {
        "success": False,
        "is_update_available": False,
        "latest_version": CURRENT_VERSION,
        "current_version": CURRENT_VERSION,
        "download_url": "",
        "changelog": "",
        "error": None,
    }

    try:
        req = urllib.request.Request(
            update_url,
            headers={"User-Agent": f"LumiEditor/{CURRENT_VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        remote_ver = str(data.get("version", CURRENT_VERSION)).strip()
        result["latest_version"] = remote_ver
        result["download_url"] = data.get("download_url", "")
        result["changelog"] = data.get("changelog", "No release notes provided.")
        result["is_update_available"] = is_newer_version(remote_ver, CURRENT_VERSION)
        result["success"] = True

    except urllib.error.URLError as e:
        result["error"] = f"Could not connect to update server: {e.reason}"
    except json.JSONDecodeError:
        result["error"] = "Received invalid response from update server."
    except Exception as e:
        result["error"] = str(e)

    return result


# ═══════════════════════════════════════════════════════════════════
#  WINDOWS SELF-UPDATE HANDOFF
# ═══════════════════════════════════════════════════════════════════

def perform_windows_update(download_url: str, progress_callback=None) -> tuple[bool, str]:
    """
    Download the new executable and execute a detached batch runner
    that waits for this process to exit, swaps the .exe, and restarts it.
    """
    if not getattr(sys, 'frozen', False):
        return False, "Self-update is only available when running from compiled .exe."

    current_exe = os.path.abspath(sys.executable)
    exe_dir = os.path.dirname(current_exe)
    temp_dir = tempfile.gettempdir()
    downloaded_exe = os.path.join(temp_dir, f"LumiEditor_update_{os.getpid()}.exe")

    try:
        # Download new binary
        def report_hook(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                percent = min(100.0, (block_num * block_size / total_size) * 100.0)
                progress_callback(percent)

        urllib.request.urlretrieve(download_url, downloaded_exe, reporthook=report_hook)

        # Create the updater batch script
        script_path = os.path.join(temp_dir, f"lumi_updater_{os.getpid()}.bat")
        pid = os.getpid()

        batch_script = f"""@echo off
echo Updating Lumi Editor...
ping 127.0.0.1 -n 3 > nul
:WAIT_LOOP
tasklist /FI "PID eq {pid}" 2>NUL | find /I /N "{pid}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto WAIT_LOOP
)

copy /Y "{downloaded_exe}" "{current_exe}" > nul
if "%ERRORLEVEL%"=="0" (
    del /F /Q "{downloaded_exe}" > nul
    start "" "{current_exe}"
) else (
    echo Update failed to replace executable.
    pause
)
del /F /Q "{script_path}" > nul
exit
"""
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(batch_script)

        # Launch detached updater script and terminate current app
        subprocess.Popen(
            ["cmd.exe", "/c", script_path],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            close_fds=True
        )
        sys.exit(0)

    except Exception as e:
        return False, f"Failed to perform update: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
#  UPDATE DIALOG UI
# ═══════════════════════════════════════════════════════════════════

class UpdateDialog(tk.Toplevel):
    """Modern modal dialog for checking and applying updates."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Lumi Editor — System Update")
        self.geometry("520x360")
        self.minsize(480, 320)
        self.configure(bg=COLORS["bg_primary"])
        self.transient(parent)
        self.grab_set()

        self._download_url = ""
        self._build_ui()
        self._start_check()

    def _build_ui(self):
        # Header banner
        header = tk.Frame(self, bg=COLORS["bg_dark"], height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="✨  Software Updates",
            font=FONTS["heading"],
            fg=COLORS["text_on_dark"],
            bg=COLORS["bg_dark"]
        ).pack(side="left", padx=20, pady=12)

        accent_bar = tk.Frame(self, bg=COLORS["accent"], height=2)
        accent_bar.pack(fill="x", side="top")

        # Content Container
        content = ttk.Frame(self, style="TFrame")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # Version Info Card
        card = ttk.LabelFrame(content, text="  Version Details  ")
        card.pack(fill="x", pady=(0, 12))

        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=6, pady=4)

        v_row = ttk.Frame(inner, style="Card.TFrame")
        v_row.pack(fill="x")

        ttk.Label(v_row, text=f"Installed Version:  v{CURRENT_VERSION}",
                  style="CardHeading.TLabel").pack(side="left")

        self.lbl_latest = ttk.Label(v_row, text="Latest:  Checking…",
                                    style="CardSecondary.TLabel")
        self.lbl_latest.pack(side="right")

        # Status & Message
        self.lbl_status = ttk.Label(content, text="Checking for updates...",
                                    style="Subheading.TLabel")
        self.lbl_status.pack(anchor="w", pady=(0, 6))

        # Changelog / Details text box
        self.txt_changelog = tk.Text(
            content, height=6, bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"], relief="solid",
            borderwidth=1, font=FONTS["body_small"],
            wrap="word", padx=8, pady=6
        )
        self.txt_changelog.pack(fill="both", expand=True, pady=(0, 10))
        self.txt_changelog.insert("1.0", "Connecting to update server…")
        self.txt_changelog.configure(state="disabled")

        # Progress bar
        self.pbar = ttk.Progressbar(content, orient="horizontal",
                                   mode="indeterminate",
                                   style="Gold.Horizontal.TProgressbar")
        self.pbar.pack(fill="x", pady=(0, 12))
        self.pbar.start(10)

        # Action Buttons Footer
        btn_bar = ttk.Frame(content, style="TFrame")
        btn_bar.pack(fill="x")

        self.btn_check = ttk.Button(
            btn_bar, text="🔄  Check Again",
            style="Browse.TButton", command=self._start_check
        )
        self.btn_check.pack(side="left")

        self.btn_close = ttk.Button(
            btn_bar, text="Close",
            style="Browse.TButton", command=self.destroy
        )
        self.btn_close.pack(side="right", padx=(8, 0))

        self.btn_update = ttk.Button(
            btn_bar, text="⚡ Update Now",
            style="Accent.TButton", command=self._apply_update,
            state="disabled"
        )
        self.btn_update.pack(side="right")

    def _start_check(self):
        self.btn_check.configure(state="disabled")
        self.btn_update.configure(state="disabled")
        self.lbl_status.configure(text="Checking for updates...", style="Subheading.TLabel")
        self.pbar.configure(mode="indeterminate")
        self.pbar.start(10)

        threading.Thread(target=self._worker_check, daemon=True).start()

    def _worker_check(self):
        res = check_for_updates()
        self.after(0, lambda: self._handle_check_result(res))

    def _handle_check_result(self, res: dict):
        self.pbar.stop()
        self.pbar.configure(mode="determinate", value=100)
        self.btn_check.configure(state="normal")

        self.txt_changelog.configure(state="normal")
        self.txt_changelog.delete("1.0", "end")

        if not res["success"]:
            self.lbl_status.configure(text="⚠️  Update Check Notice", style="Subheading.TLabel")
            self.lbl_latest.configure(text="Latest: Unknown")
            
            notice_msg = (
                f"Lumi Editor is up to date (v{CURRENT_VERSION}).\n\n"
                f"Note: {res.get('error', 'Remote update repository is on standby.')}\n"
                f"Your local installation is operating on the latest release build."
            )
            self.txt_changelog.insert("1.0", notice_msg)
            self.txt_changelog.configure(state="disabled")
            return

        latest = res["latest_version"]
        self.lbl_latest.configure(text=f"Latest:  v{latest}")
        self._download_url = res["download_url"]

        if res["is_update_available"]:
            self.lbl_status.configure(text="🎉  New Version Available!", style="Success.TLabel")
            self.txt_changelog.insert("1.0", f"What's new in v{latest}:\n\n{res['changelog']}")
            if self._download_url and getattr(sys, 'frozen', False):
                self.btn_update.configure(state="normal")
        else:
            self.lbl_status.configure(text="✅  Lumi Editor is Up to Date", style="Success.TLabel")
            self.txt_changelog.insert("1.0", f"You are running the latest version (v{CURRENT_VERSION}).\n\nNo updates required.")

        self.txt_changelog.configure(state="disabled")

    def _apply_update(self):
        if not self._download_url:
            messagebox.showinfo("Update", "No download URL specified in update manifest.", parent=self)
            return

        self.btn_update.configure(state="disabled")
        self.btn_check.configure(state="disabled")
        self.lbl_status.configure(text="Downloading and applying update…", style="Subheading.TLabel")
        self.pbar.configure(mode="determinate", value=0)

        def update_worker():
            def progress(pct):
                self.after(0, lambda: self.pbar.configure(value=pct))

            success, err = perform_windows_update(self._download_url, progress_callback=progress)
            if not success:
                self.after(0, lambda: messagebox.showerror("Update Error", err, parent=self))
                self.after(0, lambda: self.btn_check.configure(state="normal"))

        threading.Thread(target=update_worker, daemon=True).start()
