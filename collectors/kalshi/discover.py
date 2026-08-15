"""Find single-game sports markets on Kalshi by series ticker."""
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kalshi.auth import load_private_key, auth_headers  # noqa: E402

BASE = "https://api.elections.kalshi.com"

# Try common sports single-game series tickers
CANDIDATES = ["KXMLBGAME", "KXNBA", "KXNFLGAME", "KXNHL", "KXWNBA",
              "KXEPLGAME", "KXUFCFIGHT", "KXTENNIS"]


def load_key_id() -> str:
    env = Path("/home/christian/Prediction-Markets/.env")
    for line in env.read_text().splitlines():
        if line.startswith("KALSHI_KEY_ID="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no KALSHI_KEY_ID in .env")


def get(pk, key_id, path):
    headers = auth_headers(pk, key_id, "GET", path)
    r = httpx.get(BASE + path, headers=headers, timeout=30)
    return r.status_code, r.json()


if __name__ == "__main__":
    pk = load_private_key()
    key_id = load_key_id()
    for series in CANDIDATES:
        path = f"/trade-api/v2/markets?series_ticker={series}&status=open&limit=10"
        code, data = get(pk, key_id, path)
        markets = data.get("markets", []) if code == 200 else []
        print(f"\n=== {series} (status {code}, {len(markets)} markets) ===")
        for m in markets[:8]:
            print(f"  VOL={m.get('volume',0):>8} | {m.get('ticker','?'):<35} | {m.get('title','?')[:50]}")
