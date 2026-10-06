"""
Lumi Editor — Update & Version Management System
Integrates with the GitHub Releases API for automated update checking,
release notes display, and seamless Windows self-updating.
"""

import json
import os
import sys
import subprocess
import tempfile
import threading
import urllib.request
import urllib.error
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

from theme import COLORS, FONTS, ToolTip


# ═══════════════════════════════════════════════════════════════════
#  VERSION & REPOSITORY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

APP_NAME = "Lumi Editor"
CURRENT_VERSION = "1.0.1"

# Target GitHub Repository: https://github.com/sleeping-f/Lumi-Editor
GITHUB_OWNER = "sleeping-f"
GITHUB_REPO = "Lumi-Editor"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"


def parse_version(ver_str: str) -> tuple[int, ...]:
    """Parse a version tag like 'v1.2.3' or '1.2.0' into a comparable tuple."""
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
#  GITHUB RELEASES API CHECKER
# ═══════════════════════════════════════════════════════════════════

def check_for_updates(timeout: int = 7) -> dict:
    """
    Query the GitHub Releases API for the latest published release.

    Returns dict with keys:
        'success': bool
        'is_update_available': bool
        'latest_version': str
        'current_version': str
        'release_title': str
        'download_url': str
        'download_size': int (bytes)
        'html_url': str
        'changelog': str
        'error': str or None
    """
    result = {
        "success": False,
        "is_update_available": False,
        "latest_version": CURRENT_VERSION,
        "current_version": CURRENT_VERSION,
        "release_title": "",
        "download_url": "",
        "download_size": 0,
        "html_url": GITHUB_RELEASES_PAGE,
        "changelog": "",
        "error": None,
    }

    req = urllib.request.Request(
        GITHUB_API_URL,
        headers={
            "User-Agent": f"LumiEditor/{CURRENT_VERSION}",
            "Accept": "application/vnd.github.v3+json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        tag_name = str(data.get("tag_name", CURRENT_VERSION)).strip()
        result["latest_version"] = tag_name.lstrip("vV")
        result["release_title"] = data.get("name") or tag_name
        result["html_url"] = data.get("html_url", GITHUB_RELEASES_PAGE)
        result["changelog"] = data.get("body", "No release notes provided.")
        result["is_update_available"] = is_newer_version(result["latest_version"], CURRENT_VERSION)

        # Locate the compiled .exe attached asset
        assets = data.get("assets", [])
        exe_asset = None
        for a in assets:
            if a.get("name", "").lower().endswith(".exe"):
                exe_asset = a
                break

        if exe_asset:
            result["download_url"] = exe_asset.get("browser_download_url", "")
            result["download_size"] = exe_asset.get("size", 0)

        result["success"] = True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 404 means the repository exists, but no releases have been published yet
            result["success"] = True
            result["is_update_available"] = False
            result["changelog"] = (
                f"Lumi Editor is operating on the baseline build (v{CURRENT_VERSION}).\n\n"
                f"No public releases have been published on GitHub yet.\n"
                f"Repository: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
            )
        elif e.code == 403:
            # Rate limit exceeded (60 requests/hour unauthenticated)
            result["error"] = "GitHub API rate limit reached. Please view releases in your browser."
        else:
            result["error"] = f"GitHub API error (HTTP {e.code}): {e.reason}"

    except urllib.error.URLError as e:
        result["error"] = f"Could not reach GitHub: {e.reason}"
    except json.JSONDecodeError:
        result["error"] = "Received invalid JSON from GitHub API."
    except Exception as e:
        result["error"] = str(e)

    return result


# ═══════════════════════════════════════════════════════════════════
#  WINDOWS SELF-UPDATE HANDOFF
# ═══════════════════════════════════════════════════════════════════

def perform_windows_update(download_url: str, progress_callback=None) -> tuple[bool, str]:
    """
    Download the new executable from GitHub and execute a detached batch runner
    that waits for this process to exit, swaps the .exe, and restarts it.
    """
    if not getattr(sys, 'frozen', False):
        return False, "Self-update is only available when running from compiled .exe."

    current_exe = os.path.abspath(sys.executable)
    temp_dir = tempfile.gettempdir()
    downloaded_exe = os.path.join(temp_dir, f"LumiEditor_update_{os.getpid()}.exe")

    try:
        # Download new binary in chunks with progress reporting
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": f"LumiEditor/{CURRENT_VERSION}"}
        )

        with urllib.request.urlopen(req) as resp, open(downloaded_exe, "wb") as out_file:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 65536  # 64 KB chunks

            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    pct = min(100.0, (downloaded / total_size) * 100.0)
                    progress_callback(pct, downloaded, total_size)

        # Create the updater batch script
        script_path = os.path.join(temp_dir, f"lumi_updater_{os.getpid()}.bat")
        pid = os.getpid()

        batch_script = f"""@echo off
title Lumi Editor Updater
echo ========================================================
echo             UPDATING LUMI EDITOR TO LATEST RELEASE
echo ========================================================
echo.
echo Waiting for Lumi Editor process (PID {pid}) to close...
ping 127.0.0.1 -n 3 > nul

:WAIT_LOOP
tasklist /FI "PID eq {pid}" 2>NUL | find /I /N "{pid}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto WAIT_LOOP
)

echo Swapping executable to new version...
copy /Y "{downloaded_exe}" "{current_exe}" > nul
if "%ERRORLEVEL%"=="0" (
    del /F /Q "{downloaded_exe}" > nul
    echo Update complete! Restarting Lumi Editor...
    start "" "{current_exe}"
) else (
    echo [ERROR] Failed to overwrite executable. You can manually copy:
    echo "{downloaded_exe}"
    echo to:
    echo "{current_exe}"
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
        return False, f"Failed to download/apply update: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
#  UPDATE DIALOG UI
# ═══════════════════════════════════════════════════════════════════

class UpdateDialog(tk.Toplevel):
    """Modern modal dialog for checking GitHub Releases and applying updates."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Lumi Editor — Software Updates")
        self.geometry("560x420")
        self.minsize(500, 360)
        self.configure(bg=COLORS["bg_primary"])
        self.transient(parent)
        self.grab_set()

        self._download_url = ""
        self._html_url = GITHUB_RELEASES_PAGE
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

        tk.Label(
            header,
            text="GitHub Releases",
            font=FONTS["body_small"],
            fg=COLORS["accent"],
            bg=COLORS["bg_dark"]
        ).pack(side="right", padx=20, pady=16)

        accent_bar = tk.Frame(self, bg=COLORS["accent"], height=2)
        accent_bar.pack(fill="x", side="top")

        # Content Container
        content = ttk.Frame(self, style="TFrame")
        content.pack(fill="both", expand=True, padx=22, pady=14)

        # Version Info Card
        card = ttk.LabelFrame(content, text="  Version Information  ")
        card.pack(fill="x", pady=(0, 10))

        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=6, pady=4)

        v_row = ttk.Frame(inner, style="Card.TFrame")
        v_row.pack(fill="x")

        ttk.Label(v_row, text=f"Installed:  v{CURRENT_VERSION}",
                  style="CardHeading.TLabel").pack(side="left")

        self.lbl_latest = ttk.Label(v_row, text="Latest:  Checking…",
                                    style="CardSecondary.TLabel")
        self.lbl_latest.pack(side="right")

        # Developer Credit
        dev_row = ttk.Frame(inner, style="Card.TFrame")
        dev_row.pack(fill="x", pady=(4, 0))
        ttk.Label(dev_row, text="Developed by Md. Farhan Sadique",
                  style="CardSecondary.TLabel").pack(side="left")

        # Status & Message
        self.lbl_status = ttk.Label(content, text="Checking GitHub for releases...",
                                    style="Subheading.TLabel")
        self.lbl_status.pack(anchor="w", pady=(0, 4))

        # Changelog / Details text box
        self.txt_changelog = tk.Text(
            content, height=8, bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"], relief="solid",
            borderwidth=1, font=FONTS["body_small"],
            wrap="word", padx=10, pady=8
        )
        self.txt_changelog.pack(fill="both", expand=True, pady=(0, 8))
        self.txt_changelog.insert("1.0", "Connecting to GitHub Releases API…")
        self.txt_changelog.configure(state="disabled")

        # Progress bar & label
        self.pbar_frame = ttk.Frame(content, style="TFrame")
        self.pbar_frame.pack(fill="x", pady=(0, 10))

        self.pbar = ttk.Progressbar(self.pbar_frame, orient="horizontal",
                                   mode="indeterminate",
                                   style="Gold.Horizontal.TProgressbar")
        self.pbar.pack(fill="x")
        self.pbar.start(10)

        self.lbl_progress_info = ttk.Label(self.pbar_frame, text="", style="Secondary.TLabel")
        self.lbl_progress_info.pack(anchor="w", pady=(2, 0))

        # Action Buttons Footer
        btn_bar = ttk.Frame(content, style="TFrame")
        btn_bar.pack(fill="x")

        self.btn_check = ttk.Button(
            btn_bar, text="🔄  Check Again",
            style="Browse.TButton", command=self._start_check
        )
        self.btn_check.pack(side="left")

        self.btn_github = ttk.Button(
            btn_bar, text="🌐  View on GitHub",
            style="Browse.TButton", command=self._open_github
        )
        self.btn_github.pack(side="left", padx=(8, 0))
        ToolTip(self.btn_github, "Open releases page in web browser")

        self.btn_close = ttk.Button(
            btn_bar, text="Close",
            style="Browse.TButton", command=self.destroy
        )
        self.btn_close.pack(side="right", padx=(8, 0))

        self.btn_update = ttk.Button(
            btn_bar, text="⚡ Update & Restart",
            style="Accent.TButton", command=self._apply_update,
            state="disabled"
        )
        self.btn_update.pack(side="right")

    def _open_github(self):
        webbrowser.open(self._html_url or GITHUB_RELEASES_PAGE)

    def _start_check(self):
        self.btn_check.configure(state="disabled")
        self.btn_update.configure(state="disabled")
        self.lbl_status.configure(text="Connecting to GitHub Releases API...", style="Subheading.TLabel")
        self.lbl_progress_info.configure(text="")
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
            self.lbl_status.configure(text="⚠️  Notice", style="Subheading.TLabel")
            self.lbl_latest.configure(text="Latest: Unknown")
            notice_msg = f"{res.get('error', 'Could not retrieve releases.')}\n\nYou can click 'View on GitHub' to check releases manually in your browser."
            self.txt_changelog.insert("1.0", notice_msg)
            self.txt_changelog.configure(state="disabled")
            return

        latest = res["latest_version"]
        self.lbl_latest.configure(text=f"Latest:  v{latest}")
        self._download_url = res["download_url"]
        self._html_url = res["html_url"]

        if res["is_update_available"]:
            self.lbl_status.configure(text=f"🎉  New Release Available: v{latest}!", style="Success.TLabel")
            title = res["release_title"]
            notes = res["changelog"]

            size_str = ""
            if res["download_size"]:
                size_mb = res["download_size"] / (1024 * 1024)
                size_str = f" ({size_mb:.1f} MB)"

            info = f"Release: {title}\nVersion: v{latest}{size_str}\n\nWhat's New:\n{notes}"
            self.txt_changelog.insert("1.0", info)

            if getattr(sys, 'frozen', False):
                if self._download_url:
                    self.btn_update.configure(state="normal")
                else:
                    self.lbl_progress_info.configure(
                        text="No .exe attached to this GitHub release yet. Click 'View on GitHub' for details."
                    )
            else:
                self.lbl_progress_info.configure(
                    text="Running in Python development mode. Click 'View on GitHub' to inspect release."
                )
        else:
            self.lbl_status.configure(text="✅  Lumi Editor is Up to Date", style="Success.TLabel")
            self.txt_changelog.insert("1.0", res["changelog"] or f"You are running the latest version (v{CURRENT_VERSION}).\n\nNo updates required.")

        self.txt_changelog.configure(state="disabled")

    def _apply_update(self):
        if not self._download_url:
            messagebox.showinfo("Update", "No .exe download URL found in this release.", parent=self)
            return

        self.btn_update.configure(state="disabled")
        self.btn_check.configure(state="disabled")
        self.btn_github.configure(state="disabled")
        self.lbl_status.configure(text="Downloading update from GitHub...", style="Subheading.TLabel")
        self.pbar.configure(mode="determinate", value=0)

        def update_worker():
            def progress(pct, downloaded, total):
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                info_text = f"Downloading: {mb_down:.1f} MB / {mb_total:.1f} MB ({int(pct)}%)"
                self.after(0, lambda: self.pbar.configure(value=pct))
                self.after(0, lambda: self.lbl_progress_info.configure(text=info_text))

            success, err = perform_windows_update(self._download_url, progress_callback=progress)
            if not success:
                self.after(0, lambda: messagebox.showerror("Update Error", err, parent=self))
                self.after(0, lambda: self.btn_check.configure(state="normal"))
                self.after(0, lambda: self.btn_github.configure(state="normal"))

        threading.Thread(target=update_worker, daemon=True).start()
