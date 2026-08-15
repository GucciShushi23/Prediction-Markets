"""Fetch open MLB single-game markets and write them to kalshi_universe.json.

Run daily (or before starting the collector) to refresh the ticker list.
Add more series to SERIES to expand (e.g. KXNFLGAME once NFL season starts).
"""
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kalshi.auth import load_private_key, auth_headers  # noqa: E402

BASE = "https://api.elections.kalshi.com"
SERIES = ["KXMLBGAME"]  # add "KXNFLGAME" etc. to expand
OUT = Path(__file__).resolve().parents[2] / "config" / "kalshi_universe.json"


def load_key_id() -> str:
    env = Path(__file__).resolve().parents[2] / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("KALSHI_KEY_ID="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no KALSHI_KEY_ID in .env")


def get(pk, key_id, path):
    headers = auth_headers(pk, key_id, "GET", path)
    r = httpx.get(BASE + path, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    pk = load_private_key()
    key_id = load_key_id()
    tickers = []
    labels = {}
    for series in SERIES:
        cursor = None
        while True:
            path = f"/trade-api/v2/markets?series_ticker={series}&status=open&limit=200"
            if cursor:
                path += f"&cursor={cursor}"
            data = get(pk, key_id, path)
            for m in data.get("markets", []):
                t = m.get("ticker")
                if t:
                    tickers.append(t)
                    labels[t] = m.get("title", "")
            cursor = data.get("cursor")
            if not cursor:
                break
    OUT.write_text(json.dumps({"tickers": tickers, "labels": labels}, indent=2))
    print(f"wrote {len(tickers)} tickers to {OUT}")
