"""
Render Web service entrypoint: Gunicorn (Flask OAuth) + Telegram bot polling.

Uses Python instead of bash so Windows CRLF in .sh files cannot break Linux deploys.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    extra = str(SRC)
    existing = env.get("PYTHONPATH", "")
    if existing:
        env["PYTHONPATH"] = f"{extra}{os.pathsep}{existing}"
    else:
        env["PYTHONPATH"] = extra
    # So bot tracebacks and prints show up in Render logs immediately.
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def main() -> int:
    env = _child_env()
    port = os.environ.get("PORT", "8000")
    bot: subprocess.Popen | None = None

    gunicorn = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gunicorn",
            "--chdir",
            str(SRC),
            "callback_server:app",
            "--bind",
            f"0.0.0.0:{port}",
            "--workers",
            "1",
            "--threads",
            "2",
            "--timeout",
            "120",
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
        ],
        cwd=str(ROOT),
        env=env,
    )

    # Give Gunicorn time to bind before Render's HTTP health check runs.
    time.sleep(2)
    if gunicorn.poll() is not None:
        code = gunicorn.returncode
        sys.stderr.write(
            f"render_entry: gunicorn exited immediately (code={code}). "
            "Check Render logs for ImportError or missing dependencies.\n"
        )
        return code if code is not None else 1

    bot = subprocess.Popen(
        [sys.executable, str(SRC / "bot.py")],
        cwd=str(ROOT),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    time.sleep(4)
    if bot.poll() is not None:
        sys.stderr.write(
            f"render_entry: Telegram bot subprocess exited early (code={bot.returncode}). "
            "Set TELEGRAM_BOT_TOKEN or Telegram_API on Render; "
            "stop any other instance using the same token (local run, second host).\n"
        )

    def shutdown(*_: object) -> None:
        for proc in (gunicorn, bot):
            if proc is None:
                continue
            if proc.poll() is None:
                proc.terminate()
        deadline = time.time() + 25
        for proc in (gunicorn, bot):
            if proc is None:
                continue
            while proc.poll() is None and time.time() < deadline:
                time.sleep(0.2)
            if proc.poll() is None:
                proc.kill()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        rc = gunicorn.wait()
        return int(rc or 0)
    finally:
        shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
