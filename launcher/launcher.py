"""
World Intelligence Platform — Main Launcher
Supports: Windows 8/10/11, macOS 11+, Linux (GTK / AppIndicator)

Author    : Muhammad Umer Lari
Copyright : © 2024-2025 Muhammad Umer Lari. All Rights Reserved.
Contact   : umerlari1998@gmail.com

Double-click (or install via setup) to:
  1. Start the FastAPI backend silently in the background
  2. Open the dashboard in the default browser
  3. Show a system-tray icon with menu
  4. Silently check for updates and prompt if a new version is available
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path

# ── Runtime metadata ──────────────────────────────────────────
PLATFORM = platform.system()          # 'Windows' | 'Darwin' | 'Linux'

# Resolve paths whether running as .py or PyInstaller .exe / .app
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _BASE = Path(sys._MEIPASS)
else:
    _BASE = Path(__file__).resolve().parent.parent   # repo root

# Import version constants (bundled with the exe)
try:
    sys.path.insert(0, str(_BASE))
    from version import (
        APP_NAME, APP_VERSION, APP_AUTHOR, APP_COPYRIGHT,
        BACKEND_HOST, BACKEND_PORT, DASHBOARD_FILE,
    )
except ImportError:
    APP_NAME       = "World Intelligence Platform"
    APP_VERSION    = "3.4.0"
    APP_AUTHOR     = "Muhammad Umer Lari"
    APP_COPYRIGHT  = "Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved."
    BACKEND_HOST   = "127.0.0.1"
    BACKEND_PORT   = 8111
    DASHBOARD_FILE = "dashboard/world-intelligence.html"


def base_path(rel: str) -> Path:
    """Resolve a path relative to the bundle root."""
    return _BASE / rel


# ─────────────────────────────────────────────────────────────
#  Single-instance guard
# ─────────────────────────────────────────────────────────────
_LOCK_FILE_HANDLE = None   # keep reference so POSIX file lock persists

def _ensure_single_instance() -> None:
    """Prevent more than one copy from running at the same time."""
    global _LOCK_FILE_HANDLE

    if PLATFORM == "Windows":
        import ctypes
        _MUTEX_NAME = "WorldIntelligencePlatform_MUX_MuhammadUmerLari"
        ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
            sys.exit(0)
    else:
        # POSIX (macOS / Linux): advisory file lock
        import fcntl
        lock_path = Path(tempfile.gettempdir()) / "WorldIntelligence_MUL.lock"
        try:
            f = open(lock_path, "w")
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _LOCK_FILE_HANDLE = f   # keep open so lock stays
        except OSError:
            sys.exit(0)


# ─────────────────────────────────────────────────────────────
#  Backend server management
# ─────────────────────────────────────────────────────────────

def _backend_script() -> Path:
    """Locate market_server.py — inside bundle or in repo."""
    candidates = [
        base_path("backend/market_server.py"),
        Path(__file__).resolve().parent.parent / "backend" / "market_server.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("market_server.py not found")


def start_backend() -> subprocess.Popen:
    """Launch the FastAPI backend invisibly in the background."""
    script = str(_backend_script())
    env    = os.environ.copy()
    env["PORT"] = str(BACKEND_PORT)

    if PLATFORM == "Windows":
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(
            [sys.executable, script],
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
    else:
        # macOS / Linux — detach from current session, suppress output
        proc = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=env,
        )
    return proc


def wait_for_backend(timeout: int = 25) -> bool:
    """Poll until the backend TCP port is open."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((BACKEND_HOST, BACKEND_PORT), timeout=1):
                return True
        except OSError:
            time.sleep(0.4)
    return False


# ─────────────────────────────────────────────────────────────
#  Dashboard opener
# ─────────────────────────────────────────────────────────────

def open_dashboard() -> None:
    """Open the dashboard — prefer live server, fall back to local file."""
    try:
        with socket.create_connection((BACKEND_HOST, BACKEND_PORT), timeout=2):
            webbrowser.open(f"http://{BACKEND_HOST}:{BACKEND_PORT}")
            return
    except OSError:
        pass
    local = base_path(DASHBOARD_FILE)
    if local.exists():
        webbrowser.open(local.as_uri())


def _open_when_ready() -> None:
    """Background thread: wait for backend then open browser."""
    if wait_for_backend():
        open_dashboard()
    else:
        open_dashboard()   # local file fallback


# ─────────────────────────────────────────────────────────────
#  Notifications (cross-platform)
# ─────────────────────────────────────────────────────────────

def _notify(message: str) -> None:
    if PLATFORM == "Windows":
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x40)
    elif PLATFORM == "Darwin":
        safe = message.replace('"', "'")
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{safe}" with title "{APP_NAME}"'],
            check=False,
        )
    else:
        try:
            subprocess.run(
                ["notify-send", APP_NAME, message],
                check=False, timeout=3,
            )
        except FileNotFoundError:
            pass


# ─────────────────────────────────────────────────────────────
#  System tray icon
# ─────────────────────────────────────────────────────────────

def _tray_icon_image() -> "PIL.Image.Image":
    """Load bundled icon.png; draw a minimal fallback if not found."""
    from PIL import Image

    # Look for the icon in several places
    candidates = [
        base_path("launcher/build/icon.png"),
        Path(__file__).resolve().parent / "build" / "icon.png",
        base_path("icon.png"),
    ]
    for p in candidates:
        if p.exists():
            return Image.open(p).convert("RGBA").resize((64, 64))

    # Minimal fallback drawing
    from PIL import ImageDraw
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, 62, 62], fill=(8, 17, 38, 255))
    draw.ellipse([2, 2, 62, 62], outline=(0, 200, 220, 255), width=3)
    draw.ellipse([27, 27, 37, 37], fill=(52, 211, 153, 255))
    return img


def run_tray() -> None:
    """Run the system-tray icon — blocks until user chooses Quit."""
    import pystray
    from pystray import MenuItem as Item, Menu

    def on_open(_icon, _item):    open_dashboard()
    def on_quit(icon,  _item):    icon.stop()

    def on_update(_icon, _item):
        try:
            from updater import check_and_update
            check_and_update(silent=False)
        except Exception as e:
            _notify(f"Update check failed:\n{e}")

    def on_about(_icon, _item):
        _notify(
            f"{APP_NAME}\n"
            f"Version  : {APP_VERSION}\n"
            f"Author   : {APP_AUTHOR}\n"
            f"Platform : {PLATFORM}\n"
            f"{APP_COPYRIGHT}"
        )

    menu = Menu(
        Item("Open Dashboard",   on_open,   default=True),
        Menu.SEPARATOR,
        Item("Check for Updates", on_update),
        Item("About",            on_about),
        Menu.SEPARATOR,
        Item("Quit",             on_quit),
    )

    icon = pystray.Icon(
        name=APP_NAME,
        icon=_tray_icon_image(),
        title=f"{APP_NAME} v{APP_VERSION}\n© {APP_AUTHOR}",
        menu=menu,
    )
    icon.run()


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────

def main() -> None:
    # 1. Block duplicate instances
    _ensure_single_instance()

    # 2. Start the FastAPI backend (silent, detached)
    try:
        start_backend()
    except FileNotFoundError:
        _notify("Backend script not found.\nPlease reinstall the application.")
        sys.exit(1)

    # 3. Open browser as soon as server is ready (background thread)
    threading.Thread(target=_open_when_ready, daemon=True).start()

    # 4. Delayed background update check — 8 s after launch
    def _bg_update():
        time.sleep(8)
        try:
            from updater import check_and_update
            check_and_update(silent=True)
        except Exception:
            pass

    threading.Thread(target=_bg_update, daemon=True).start()

    # 5. System tray (blocks until Quit)
    run_tray()


if __name__ == "__main__":
    main()
