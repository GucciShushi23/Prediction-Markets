"""Health check for the Kalshi collector."""
import os
import sys
import time
import glob
from pathlib import Path

import httpx

STALE_AFTER_SECONDS = 600
DATA_GLOB = "/home/christian/Prediction-Markets/data/raw/kalshi/*/*.jsonl"
ENV_PATH = Path("/home/christian/Prediction-Markets/.env")
DISCORD_MENTION = "<@727538215568801872>"


def load_env(key):
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def newest_file_age():
    files = glob.glob(DATA_GLOB)
    if not files:
        return None
    return time.time() - os.path.getmtime(max(files, key=os.path.getmtime))


def discord_alert(msg):
    url = load_env("DISCORD_WEBHOOK_URL")
    if url:
        try:
            httpx.post(url, json={"content": msg}, timeout=15)
        except Exception as e:
            print(f"discord fail: {e}", file=sys.stderr)


def hc_ping():
    url = load_env("KALSHI_HEALTHCHECK_URL")
    if url:
        try:
            httpx.get(url, timeout=15)
        except Exception as e:
            print(f"hc fail: {e}", file=sys.stderr)


if __name__ == "__main__":
    age = newest_file_age()
    if age is None:
        discord_alert(f"{DISCORD_MENTION} 🔴 Kalshi collector: NO data files found.")
    elif age > STALE_AFTER_SECONDS:
        discord_alert(f"{DISCORD_MENTION} 🔴 Kalshi collector STALLED — {int(age//60)} min no data.")
    else:
        hc_ping()
        print(f"ok: kalshi data {int(age)}s old, pinged healthchecks")
