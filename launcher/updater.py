"""
World Intelligence Platform — Auto-Updater
Supports: Windows 8/10/11  |  macOS 11+  |  Linux

Author    : Muhammad Umer Lari
Copyright : © 2024-2025 Muhammad Umer Lari. All Rights Reserved.
Contact   : umerlari1998@gmail.com

Flow:
  1. Fetch latest release from GitHub (PUBLIC companion repo / Gist)
  2. Compare version — if newer, ask user
  3. Download new exe/binary
  4. Verify SHA-256 from release notes
  5. Apply update:
       Windows → .bat waits for PID exit, copies file, relaunches
       macOS   → .sh  waits for PID exit, replaces .app, relaunches
       Linux   → .sh  waits for PID exit, replaces binary, relaunches
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import httpx
    _HTTP_LIB = "httpx"
except ImportError:
    import urllib.request as _urllib_request
    _HTTP_LIB = "urllib"

# ── Platform ──────────────────────────────────────────────────
PLATFORM = platform.system()          # 'Windows' | 'Darwin' | 'Linux'

# ── Constants ─────────────────────────────────────────────────
try:
    from version import APP_VERSION, APP_NAME, APP_AUTHOR, APP_UPDATE_URL
    _CURRENT = tuple(int(x) for x in APP_VERSION.split("."))
except ImportError:
    APP_VERSION  = "3.4.0"
    APP_NAME     = "World Intelligence Platform"
    APP_AUTHOR   = "Muhammad Umer Lari"
    # PUBLIC update endpoint — works even when source repo is private.
    # Point this at a public GitHub repo, Gist, or any free JSON endpoint.
    APP_UPDATE_URL = (
        "https://api.github.com/repos/lari98/ai-churn-analytics-platform/releases/latest"
    )
    _CURRENT = (3, 4, 0)

# Map platform to the expected asset filename suffix in GitHub Releases
_ASSET_SUFFIX = {
    "Windows": ".exe",
    "Darwin":  ".dmg",
    "Linux":   "-linux",
}


# ─────────────────────────────────────────────────────────────
#  HTTP helpers
# ─────────────────────────────────────────────────────────────

def _get_json(url: str) -> dict:
    headers = {"User-Agent": f"WorldIntelligence-Updater/{APP_VERSION}"}
    if _HTTP_LIB == "httpx":
        r = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        r.raise_for_status()
        return r.json()
    else:
        req = _urllib_request.Request(url, headers=headers)
        with _urllib_request.urlopen(req, timeout=10) as resp:
            import json
            return json.loads(resp.read())


def _download_file(url: str, dest: Path) -> None:
    headers = {"User-Agent": f"WorldIntelligence-Updater/{APP_VERSION}"}
    if _HTTP_LIB == "httpx":
        with httpx.stream("GET", url, headers=headers,
                          timeout=120, follow_redirects=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_bytes(65536):
                    f.write(chunk)
    else:
        req = _urllib_request.Request(url, headers=headers)
        with _urllib_request.urlopen(req, timeout=120) as resp, \
             open(dest, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)


# ─────────────────────────────────────────────────────────────
#  Version & release parsing
# ─────────────────────────────────────────────────────────────

def _fetch_latest_release() -> tuple[str, str, str, str]:
    """
    Returns (tag, asset_url, sha256, body) from the latest GitHub release.
    Raises if nothing found.
    """
    data  = _get_json(APP_UPDATE_URL)
    tag   = data.get("tag_name", "")
    body  = data.get("body", "")

    suffix = _ASSET_SUFFIX.get(PLATFORM, ".exe")
    asset_url = ""
    for asset in data.get("assets", []):
        if asset["name"].endswith(suffix):
            asset_url = asset["browser_download_url"]
            break

    # SHA-256 is embedded in the release body as:  SHA256=<hex>
    sha256 = ""
    m = re.search(r"SHA256=([a-fA-F0-9]{64})", body)
    if m:
        sha256 = m.group(1).lower()

    return tag, asset_url, sha256, body


def _is_newer(remote_tag: str) -> bool:
    """Return True if remote_tag is strictly newer than the running version."""
    clean = remote_tag.lstrip("v").strip()
    try:
        remote = tuple(int(x) for x in clean.split("."))
    except ValueError:
        return False
    return remote > _CURRENT


# ─────────────────────────────────────────────────────────────
#  SHA-256 verification
# ─────────────────────────────────────────────────────────────

def _verify_sha256(path: Path, expected: str) -> bool:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected.lower()


# ─────────────────────────────────────────────────────────────
#  User prompt (cross-platform)
# ─────────────────────────────────────────────────────────────

def _ask_user(message: str) -> bool:
    """Return True if the user says yes."""
    if PLATFORM == "Windows":
        import ctypes
        MB_YESNO   = 0x04
        ICON_INFO  = 0x40
        result = ctypes.windll.user32.MessageBoxW(0, message, APP_NAME,
                                                   MB_YESNO | ICON_INFO)
        return result == 6  # IDYES
    elif PLATFORM == "Darwin":
        # osascript dialog
        safe = message.replace('"', "'")
        r = subprocess.run(
            ["osascript", "-e",
             f'button returned of (display dialog "{safe}" '
             f'buttons {{"Later", "Update Now"}} default button "Update Now")'],
            capture_output=True, text=True,
        )
        return "Update Now" in r.stdout
    else:
        # Linux — zenity / kdialog / xmessage / console fallback
        for tool in (
            ["zenity", "--question", f"--text={message}", "--title", APP_NAME],
            ["kdialog", "--yesno", message, "--title", APP_NAME],
        ):
            try:
                r = subprocess.run(tool, timeout=60)
                return r.returncode == 0
            except FileNotFoundError:
                continue
        # Console fallback
        try:
            print(f"\n{APP_NAME} Update\n{message}")
            ans = input("Update now? [y/N]: ").strip().lower()
            return ans == "y"
        except Exception:
            return False


def _notify_error(message: str) -> None:
    if PLATFORM == "Windows":
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
    elif PLATFORM == "Darwin":
        safe = message.replace('"', "'")
        subprocess.run(
            ["osascript", "-e",
             f'display alert "{APP_NAME}" message "{safe}"'],
            check=False,
        )
    else:
        try:
            subprocess.run(["notify-send", "--urgency=critical",
                            APP_NAME, message], check=False, timeout=3)
        except FileNotFoundError:
            print(f"[ERROR] {message}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────
#  Apply update (replace binary and relaunch)
# ─────────────────────────────────────────────────────────────

def _apply_update(new_file: Path) -> None:
    """
    Replace the running executable with new_file and relaunch.
    Uses a small script that waits for the current PID to exit.
    """
    current_exe = Path(sys.executable)
    pid         = os.getpid()

    if PLATFORM == "Windows":
        # .bat: wait for our PID to exit, copy, relaunch, clean up
        bat = (
            f"@echo off\n"
            f":wait\n"
            f"tasklist /FI \"PID eq {pid}\" | find \"{pid}\" >nul 2>&1\n"
            f"if not errorlevel 1 (timeout /t 1 /nobreak >nul & goto wait)\n"
            f"copy /Y \"{new_file}\" \"{current_exe}\"\n"
            f"start \"\" \"{current_exe}\"\n"
            f"del \"%~f0\"\n"
        )
        bat_path = Path(tempfile.gettempdir()) / "wip_update.bat"
        bat_path.write_text(bat, encoding="utf-8")
        subprocess.Popen(
            ["cmd.exe", "/c", str(bat_path)],
            creationflags=0x00000008,   # DETACHED_PROCESS
        )

    else:
        # POSIX (.sh): wait, replace (or replace .app bundle on macOS), relaunch
        if PLATFORM == "Darwin" and current_exe.suffix == "" \
                and ".app" in str(current_exe):
            # macOS .app bundle — replace the whole .app directory
            app_path = Path(str(current_exe).split(".app")[0] + ".app")
            copy_cmd = f'cp -Rf "{new_file}" "{app_path}"'
            launch_cmd = f'open "{app_path}"'
        else:
            copy_cmd   = f'cp -f "{new_file}" "{current_exe}"'
            launch_cmd = f'"{current_exe}"'

        sh = (
            "#!/bin/bash\n"
            f"while kill -0 {pid} 2>/dev/null; do sleep 1; done\n"
            f"{copy_cmd}\n"
            f"chmod +x \"{current_exe}\"\n"
            f"nohup {launch_cmd} &>/dev/null &\n"
            "rm -- \"$0\"\n"
        )
        sh_path = Path(tempfile.gettempdir()) / "wip_update.sh"
        sh_path.write_text(sh)
        sh_path.chmod(sh_path.stat().st_mode | stat.S_IEXEC)
        subprocess.Popen(["bash", str(sh_path)],
                         close_fds=True, start_new_session=True)

    sys.exit(0)


# ─────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────

def check_and_update(silent: bool = True) -> None:
    """
    Main update flow.
    silent=True  → only show dialog if update is available
    silent=False → always show result
    """
    try:
        tag, asset_url, sha256, _ = _fetch_latest_release()
    except Exception as exc:
        if not silent:
            _notify_error(f"Cannot reach update server:\n{exc}")
        return

    if not _is_newer(tag):
        if not silent:
            if PLATFORM == "Windows":
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"You are on the latest version ({APP_VERSION}).\n"
                    f"© {APP_AUTHOR}",
                    APP_NAME, 0x40,
                )
            else:
                _notify_error(
                    f"You are on the latest version ({APP_VERSION})."
                )
        return

    if not asset_url:
        if not silent:
            _notify_error(
                f"Update {tag} is available but no installer was found "
                f"for {PLATFORM}.\n"
                f"Visit: https://github.com/lari98/ai-churn-analytics-platform/releases"
            )
        return

    # Ask user
    prompt = (
        f"A new version of {APP_NAME} is available!\n\n"
        f"Current  : v{APP_VERSION}\n"
        f"Latest   : {tag}\n\n"
        f"Download and update now?"
    )
    if not _ask_user(prompt):
        return

    # Download
    suffix   = _ASSET_SUFFIX.get(PLATFORM, ".exe")
    tmp_path = Path(tempfile.gettempdir()) / f"WorldIntelligence_update{suffix}"
    try:
        _download_file(asset_url, tmp_path)
    except Exception as exc:
        _notify_error(f"Download failed:\n{exc}")
        return

    # Verify SHA-256
    if sha256 and not _verify_sha256(tmp_path, sha256):
        tmp_path.unlink(missing_ok=True)
        _notify_error(
            "Update file failed integrity check (SHA-256 mismatch).\n"
            "Download may be corrupted. Please try again."
        )
        return

    # Apply
    _apply_update(tmp_path)


def check_pre_install() -> bool:
    """
    Called by Inno Setup Pascal stub before installation begins.
    Returns True if safe to proceed, False if user chose to abort.
    """
    try:
        tag, _, _, _ = _fetch_latest_release()
    except Exception:
        return True   # no internet — proceed

    if not _is_newer(tag):
        return True

    prompt = (
        f"A newer version ({tag}) is already available online.\n\n"
        f"You are about to install : v{APP_VERSION}\n"
        f"Latest version available : {tag}\n\n"
        f"Recommended: download the latest installer from GitHub.\n\n"
        f"Continue with this older version anyway?"
    )
    return _ask_user(prompt)
