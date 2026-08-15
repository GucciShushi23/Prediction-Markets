"""Health check: ping Healthchecks.io when healthy; alert Discord when stalled.

Run on a cron schedule. If the newest data file is fresh, ping Healthchecks.io
(so its "dead man's switch" stays satisfied). If stale, skip the ping AND alert
Discord — the missing ping makes Healthchecks.io email you too.
"""
import os
import sys
import time
import glob
from pathlib import Path

import httpx

STALE_AFTER_SECONDS = 600  # 10 minutes

DATA_GLOB = "/home/christian/Prediction-Markets/data/raw/polymarket/*/*.jsonl"
ENV_PATH = Path("/home/christian/Prediction-Markets/.env")
DISCORD_MENTION = "<@727538215568801872>"


def load_env(key: str) -> str | None:
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def newest_file_age() -> float | None:
    files = glob.glob(DATA_GLOB)
    if not files:
        return None
    newest = max(files, key=os.path.getmtime)
    return time.time() - os.path.getmtime(newest)


def discord_alert(message: str) -> None:
    url = load_env("DISCORD_WEBHOOK_URL")
    if not url:
        return
    try:
        httpx.post(url, json={"content": message}, timeout=15)
    except Exception as e:
        print(f"failed to send discord alert: {e}", file=sys.stderr)


def healthcheck_ping() -> None:
    url = load_env("HEALTHCHECK_URL")
    if not url:
        return
    try:
        httpx.get(url, timeout=15)
    except Exception as e:
        print(f"failed to ping healthchecks: {e}", file=sys.stderr)


if __name__ == "__main__":
    age = newest_file_age()
    if age is None:
        discord_alert(f"{DISCORD_MENTION} 🔴 Polymarket collector: NO data files found.")
        # No healthcheck ping — silence triggers the email alert.
    elif age > STALE_AFTER_SECONDS:
        mins = int(age // 60)
        discord_alert(f"{DISCORD_MENTION} 🔴 Polymarket collector STALLED — no new data for {mins} min.")
        # No healthcheck ping — silence triggers the email alert.
    else:
        healthcheck_ping()  # I'm alive
        print(f"ok: newest data {int(age)}s old, pinged healthchecks")
