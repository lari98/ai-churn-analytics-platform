"""
World Intelligence Platform — Self-Healing Watchdog Agent v1.0
═══════════════════════════════════════════════════════════════
Keeps the backend server running 24/7.

CAPABILITIES:
  ► Auto-restart   — detects crash in 30s, restarts immediately
  ► Health monitor — polls /api/health every 30 seconds
  ► GitHub watcher — checks for new commits every 60 minutes
  ► Auto-patch     — pulls new code, installs deps, hot-restarts
  ► Zero downtime  — dashboard falls back to client-side while restarting (~3s)
  ► Audit log      — every action logged to agent.log with timestamp

USAGE:
  python watchdog_agent.py          — run in foreground
  start_forever.bat                 — run minimized in background
  setup_autostart.bat               — install as Windows startup task (runs on boot)
"""

import subprocess, time, os, sys, logging, json
from pathlib import Path
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BACKEND_URL      = "http://localhost:8111/api/health"
SERVER_SCRIPT    = Path(__file__).parent / "market_server.py"
REPO_ROOT        = Path(__file__).parent.parent
LOG_FILE         = Path(__file__).parent / "agent.log"
STATE_FILE       = Path(__file__).parent / "agent_state.json"
GITHUB_REPO      = "lari98/ai-churn-analytics-platform"
GITHUB_API       = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"

HEALTH_INTERVAL  = 30      # seconds between health checks
GIT_INTERVAL     = 3600    # seconds between GitHub checks (1 hour)
STATUS_INTERVAL  = 600     # seconds between status log lines (10 min)
STARTUP_GRACE    = 6       # seconds to wait after starting server
RESTART_COOLDOWN = 5       # seconds between restart attempts

# ─── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [AGENT]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("watchdog")


class WatchdogAgent:
    def __init__(self):
        self.server_proc    = None
        self.restart_count  = 0
        self.start_time     = time.time()
        self.last_git_check = 0
        self.last_status    = 0
        self.last_sha       = self._local_sha()
        self._load_state()

    # ── State persistence ────────────────────────────────────────────────────

    def _load_state(self):
        try:
            if STATE_FILE.exists():
                s = json.loads(STATE_FILE.read_text())
                self.restart_count = s.get("restart_count", 0)
                log.info(f"Loaded state: {self.restart_count} prior restarts.")
        except Exception:
            pass

    def _save_state(self):
        try:
            STATE_FILE.write_text(json.dumps({
                "restart_count": self.restart_count,
                "last_sha":      self.last_sha,
                "updated":       datetime.utcnow().isoformat()
            }, indent=2))
        except Exception:
            pass

    # ── Git helpers ──────────────────────────────────────────────────────────

    def _local_sha(self) -> str | None:
        try:
            r = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=str(REPO_ROOT)
            )
            return r.stdout.strip() or None
        except Exception:
            return None

    def _remote_sha(self) -> str | None:
        try:
            import urllib.request
            req = urllib.request.Request(
                GITHUB_API,
                headers={"Accept": "application/vnd.github.v3+json",
                         "User-Agent": "WatchdogAgent/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())["sha"]
        except Exception as e:
            log.warning(f"GitHub API error: {e}")
            return None

    # ── Server lifecycle ─────────────────────────────────────────────────────

    def _is_running(self) -> bool:
        return self.server_proc is not None and self.server_proc.poll() is None

    def _is_healthy(self) -> bool:
        try:
            import urllib.request
            with urllib.request.urlopen(BACKEND_URL, timeout=5) as r:
                d = json.loads(r.read())
                return d.get("status") == "ok"
        except Exception:
            return False

    def _kill_port(self, port: int = 8111):
        """
        Kill any existing process already bound to our port.
        Handles the case where the server was started manually before
        the watchdog launched — prevents Errno 10048 (port in use).
        """
        try:
            if sys.platform == "win32":
                # Use shell=True + findstr — most reliable on Windows
                r = subprocess.run(
                    f"netstat -ano | findstr :{port}",
                    shell=True, capture_output=True, text=True
                )
                killed = set()
                for line in r.stdout.splitlines():
                    parts = line.strip().split()
                    # Line format: Proto  Local  Foreign  State  PID
                    # We want lines where local address ends in :port
                    if len(parts) < 5:
                        continue
                    local = parts[1]
                    if not local.endswith(f":{port}"):
                        continue
                    try:
                        pid = int(parts[-1])
                    except ValueError:
                        continue
                    if pid <= 0 or pid == os.getpid() or pid in killed:
                        continue
                    log.warning(f"  Port {port} held by PID {pid} — terminating.")
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True
                    )
                    killed.add(pid)
                if killed:
                    time.sleep(2)  # let the OS release the port
                    log.info(f"  Port {port} cleared (killed PIDs: {killed})")
            else:
                # Linux/Mac: lsof
                r = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True, text=True
                )
                killed = set()
                for pid_str in r.stdout.strip().splitlines():
                    try:
                        pid = int(pid_str.strip())
                    except ValueError:
                        continue
                    if pid != os.getpid() and pid not in killed:
                        log.warning(f"  Port {port} held by PID {pid} — terminating.")
                        subprocess.run(["kill", "-9", str(pid)], capture_output=True)
                        killed.add(pid)
                if killed:
                    time.sleep(1)
        except Exception as e:
            log.warning(f"  _kill_port({port}) error (non-fatal): {e}")

    def start_server(self):
        if self._is_running():
            return
        # Clear the port first — prevents Errno 10048 if old server is still up
        self._kill_port(8111)
        log.info(f"▶ Starting server (total starts: {self.restart_count + 1})…")
        self.server_proc = subprocess.Popen(
            [sys.executable, str(SERVER_SCRIPT)],
            cwd=str(SERVER_SCRIPT.parent),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32" else 0
        )
        time.sleep(STARTUP_GRACE)
        if self._is_running():
            self.restart_count += 1
            self._save_state()
            log.info(f"✓ Server up (PID {self.server_proc.pid})")
        else:
            log.error("✗ Server failed to start — will retry next cycle.")

    def stop_server(self, reason=""):
        if not self._is_running():
            return
        log.warning(f"⏹ Stopping server: {reason}")
        try:
            self.server_proc.terminate()
            self.server_proc.wait(timeout=10)
        except Exception:
            try:
                self.server_proc.kill()
            except Exception:
                pass
        self.server_proc = None
        time.sleep(RESTART_COOLDOWN)

    def restart_server(self, reason=""):
        log.warning(f"🔄 Restart triggered: {reason}")
        self.stop_server(reason)
        self.start_server()

    # ── GitHub auto-update ───────────────────────────────────────────────────

    def check_github(self):
        now = time.time()
        if now - self.last_git_check < GIT_INTERVAL:
            return
        self.last_git_check = now

        log.info("🔍 Checking GitHub for new commits…")
        remote = self._remote_sha()
        if not remote:
            return
        if remote == self.last_sha:
            log.info(f"  No changes (latest: {remote[:8]})")
            return

        log.info(f"  🆕 New commit detected: {remote[:8]} (was {str(self.last_sha)[:8]})")
        self._pull_and_restart(remote)

    def _pull_and_restart(self, new_sha: str):
        """Pull latest code, install new deps, hot-restart server."""
        log.info("  ⬇ Pulling latest code…")
        try:
            r = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True, text=True, cwd=str(REPO_ROOT)
            )
            if r.returncode != 0:
                log.error(f"  git pull failed:\n{r.stderr}")
                return
            log.info(f"  ✓ Pull OK: {r.stdout.strip()}")

            log.info("  📦 Installing new dependencies…")
            req_file = str(SERVER_SCRIPT.parent / "requirements.txt")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"],
                capture_output=True
            )
            log.info("  ✓ Dependencies up to date.")

            self.last_sha = new_sha
            self._save_state()
            self.restart_server(f"auto-update to {new_sha[:8]}")
            log.info(f"  ✅ Auto-update complete → {new_sha[:8]}")

        except Exception as e:
            log.error(f"  Auto-update error: {e}")

    # ── Status reporting ─────────────────────────────────────────────────────

    def _report_status(self):
        now = time.time()
        if now - self.last_status < STATUS_INTERVAL:
            return
        self.last_status = now
        uptime = int(now - self.start_time)
        h, m, s = uptime // 3600, (uptime % 3600) // 60, uptime % 60
        healthy = self._is_healthy()
        log.info(
            f"📊 Status | uptime={h}h{m}m{s}s | "
            f"restarts={self.restart_count} | "
            f"health={'✓' if healthy else '✗'} | "
            f"commit={str(self.last_sha)[:8] if self.last_sha else 'unknown'}"
        )

    # ── Main loop ────────────────────────────────────────────────────────────

    def run(self):
        log.info("═" * 60)
        log.info("  World Intelligence Watchdog Agent v1.0")
        log.info(f"  Server : {SERVER_SCRIPT}")
        log.info(f"  Repo   : {GITHUB_REPO}")
        log.info(f"  Health : every {HEALTH_INTERVAL}s")
        log.info(f"  GitHub : every {GIT_INTERVAL // 60}min")
        log.info(f"  Log    : {LOG_FILE}")
        log.info("═" * 60)

        self.start_server()
        self.last_status = time.time()  # don't report immediately

        while True:
            time.sleep(HEALTH_INTERVAL)

            # 1. Check if process died
            if not self._is_running():
                self.restart_server("process died unexpectedly")

            # 2. Health check (even if process is alive, it might be hung)
            elif not self._is_healthy():
                self.restart_server("health check returned bad response")

            # 3. GitHub auto-update
            self.check_github()

            # 4. Periodic status log
            self._report_status()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        WatchdogAgent().run()
    except KeyboardInterrupt:
        log.info("⏹ Watchdog stopped by user (Ctrl+C).")
        sys.exit(0)
