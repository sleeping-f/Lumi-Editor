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
import time
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
CURRENT_VERSION = "1.0.4"

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

def download_update_asset(download_url: str, progress_callback=None) -> tuple[bool, str, str]:
    """
    Download the new executable from GitHub to %TEMP% and generate the updater script.
    Returns (success, downloaded_exe_or_error, batch_script_path).
    """
    if not getattr(sys, 'frozen', False):
        return False, "Self-update is only available when running from compiled .exe.", ""

    current_exe = os.path.abspath(sys.executable)
    temp_dir = tempfile.gettempdir()
    downloaded_exe = os.path.join(temp_dir, f"LumiEditor_update_{os.getpid()}.exe")
    script_path = os.path.join(temp_dir, f"lumi_updater_{os.getpid()}.bat")
    pid = os.getpid()

    try:
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

        if not os.path.exists(downloaded_exe) or os.path.getsize(downloaded_exe) == 0:
            return False, "Downloaded update file is empty or missing.", ""

        # Build updater PowerShell runner script
        script_path = os.path.join(temp_dir, f"lumi_updater_{pid}.ps1")
        log_path = os.path.join(temp_dir, "lumi_updater.log")

        ps_script = f"""# Lumi Editor Automated Self-Updater
$target = "{current_exe}"
$newExe = "{downloaded_exe}"
$script = $MyInvocation.MyCommand.Path
$log = "{log_path}"

"Starting update at $(Get-Date)" | Out-File $log
"Target: $target" | Out-File $log -Append
"New: $newExe" | Out-File $log -Append

try {{
    # 1. Wait for parent process (PID {pid}) to terminate
    $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
    if ($proc) {{
        "Waiting for PID {pid}..." | Out-File $log -Append
        $proc.WaitForExit(15000)
    }}
    Start-Sleep -Milliseconds 1000

    # 2. Robust copy retry loop
    $replaced = $false
    for ($i = 0; $i -lt 20; $i++) {{
        try {{
            Copy-Item -Path $newExe -Destination $target -Force -ErrorAction Stop
            $replaced = $true
            "Replaced target on attempt $i" | Out-File $log -Append
            break
        }} catch {{
            "Attempt $i failed: $($_.Exception.Message)" | Out-File $log -Append
            Start-Sleep -Seconds 1
        }}
    }}

    # 3. Clean up and launch updated application
    if ($replaced) {{
        Remove-Item -Path $newExe -Force -ErrorAction SilentlyContinue
        "Launching: $target" | Out-File $log -Append
        Start-Process -FilePath $target
        Start-Sleep -Seconds 2
        Remove-Item -Path $script -Force -ErrorAction SilentlyContinue
    }} else {{
        "CRITICAL: Failed to replace $target after 20 retries" | Out-File $log -Append
    }}
}} catch {{
    "Fatal error: $($_.Exception.Message)" | Out-File $log -Append
}}
"""
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(ps_script)

        return True, downloaded_exe, script_path

    except Exception as e:
        return False, f"Failed to download update: {str(e)}", ""


def perform_windows_update(download_url: str, progress_callback=None) -> tuple[bool, str]:
    """Backward compatibility wrapper."""
    success, res, _ = download_update_asset(download_url, progress_callback)
    return success, res


# ═══════════════════════════════════════════════════════════════════
#  UPDATE DIALOG UI
# ═══════════════════════════════════════════════════════════════════

class UpdateDialog(tk.Toplevel):
    """Modern modal dialog for checking GitHub Releases and applying updates."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Lumi Editor — Software Updates")
        self.configure(bg=COLORS["bg_primary"])
        self.transient(parent)
        self.grab_set()

        self._download_url = ""
        self._html_url = GITHUB_RELEASES_PAGE
        self._build_ui()
        self._center_window(parent, width=1056, height=784)
        self._start_check()

    def _center_window(self, parent, width: int = 1056, height: int = 784):
        """Center modal dialog over parent window with minimum bounds."""
        self.minsize(640, 480)
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = min(width, int(sw * 0.95))
            h = min(height, int(sh * 0.90))

            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()

            # Center relative to parent window
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2

            # Clamp to screen bounds
            x = max(20, min(x, sw - w - 20))
            y = max(20, min(y, sh - h - 40))

            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            self.geometry(f"{width}x{height}")

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

        # Main Content Container
        content = ttk.Frame(self, style="TFrame")
        content.pack(fill="both", expand=True, padx=22, pady=(14, 16))

        # 1. Top Version Info Card
        card = ttk.LabelFrame(content, text="  Version Information  ")
        card.pack(side="top", fill="x", pady=(0, 10))

        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=10, pady=6)

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

        # 2. Bottom Action Buttons Bar (Packed at bottom so buttons are ALWAYS visible)
        btn_bar = ttk.Frame(content, style="TFrame")
        btn_bar.pack(side="bottom", fill="x", pady=(12, 0))

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

        # 3. Bottom Progress Bar & Info (Packed above action buttons)
        self.pbar_frame = ttk.Frame(content, style="TFrame")
        self.pbar_frame.pack(side="bottom", fill="x", pady=(0, 6))

        self.pbar = ttk.Progressbar(self.pbar_frame, orient="horizontal",
                                   mode="indeterminate",
                                   style="Gold.Horizontal.TProgressbar")
        self.pbar.pack(fill="x")
        self.pbar.start(10)

        self.lbl_progress_info = ttk.Label(self.pbar_frame, text="", style="Secondary.TLabel")
        self.lbl_progress_info.pack(anchor="w", pady=(3, 0))

        # 4. Status Heading (Under Card)
        self.lbl_status = ttk.Label(content, text="Checking GitHub for releases...",
                                    style="Subheading.TLabel")
        self.lbl_status.pack(side="top", anchor="w", pady=(0, 6))

        # 5. Changelog / Details text box (Fills remaining vertical space in center)
        txt_container = ttk.Frame(content, style="TFrame")
        txt_container.pack(side="top", fill="both", expand=True)

        self.txt_changelog = tk.Text(
            txt_container, bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"], relief="solid",
            borderwidth=1, font=FONTS["body_small"],
            wrap="word", padx=10, pady=8
        )
        self.txt_changelog.pack(fill="both", expand=True)
        self.txt_changelog.insert("1.0", "Connecting to GitHub Releases API…")
        self.txt_changelog.configure(state="disabled")

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
        self.btn_close.configure(state="disabled")
        self.lbl_status.configure(text="Downloading update from GitHub...", style="Subheading.TLabel")
        self.pbar.configure(mode="determinate", value=0)

        def update_worker():
            def progress(pct, downloaded, total):
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                info_text = f"Downloading: {mb_down:.1f} MB / {mb_total:.1f} MB ({int(pct)}%)"
                self.after(0, lambda: self.pbar.configure(value=pct))
                self.after(0, lambda: self.lbl_progress_info.configure(text=info_text))

            success, path_or_err, script_path = download_update_asset(
                self._download_url, progress_callback=progress
            )

            if success:
                self.after(0, lambda: self._execute_restart(script_path))
            else:
                self.after(0, lambda: self._on_download_failed(path_or_err))

        threading.Thread(target=update_worker, daemon=True).start()

    def _on_download_failed(self, error_message: str):
        messagebox.showerror("Update Error", error_message, parent=self)
        self.btn_check.configure(state="normal")
        self.btn_github.configure(state="normal")
        self.btn_close.configure(state="normal")
        self.lbl_status.configure(text="Update failed.", style="Subheading.TLabel")

    def _execute_restart(self, script_path: str):
        self.lbl_status.configure(text="⚡  Update Downloaded! Restarting Lumi Editor...", style="Success.TLabel")
        self.lbl_progress_info.configure(text="Applying update and launching new version...")
        self.pbar.configure(value=100)
        self.update()

        # Brief delay to guarantee UI repaints before terminating
        time.sleep(0.3)

        # Launch detached PowerShell runner completely independent of this process
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", script_path,
            ],
            creationflags=creationflags,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )

        # Immediately terminate the current process so Windows releases the executable file lock
        os._exit(0)
