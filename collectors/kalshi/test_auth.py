"""Prove Kalshi auth works: fetch account balance (a signed, private endpoint)."""
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kalshi.auth import load_private_key, auth_headers  # noqa: E402


def load_key_id() -> str:
    env = Path("/home/christian/Prediction-Markets/.env")
    for line in env.read_text().splitlines():
        if line.startswith("KALSHI_KEY_ID="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no KALSHI_KEY_ID in .env")


BASE = "https://api.elections.kalshi.com"
PATH = "/trade-api/v2/portfolio/balance"

if __name__ == "__main__":
    pk = load_private_key()
    key_id = load_key_id()
    headers = auth_headers(pk, key_id, "GET", PATH)
    r = httpx.get(BASE + PATH, headers=headers, timeout=15)
    print("status:", r.status_code)
    print("body:", r.text)
