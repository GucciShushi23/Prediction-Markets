"""Kalshi order book collector. Writes raw messages + recv timestamp."""
import asyncio
import json
import sys
from pathlib import Path

import structlog
import websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kalshi.auth import load_private_key, auth_headers  # noqa: E402
from common.writer import DailyWriter  # noqa: E402

WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"
WS_PATH = "/trade-api/ws/v2"
CONFIG = Path(__file__).resolve().parents[2] / "config" / "kalshi_universe.json"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
HEARTBEAT = Path("kalshi_collector.heartbeat")

log = structlog.get_logger()


def load_key_id() -> str:
    env = Path(__file__).resolve().parents[2] / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("KALSHI_KEY_ID="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no KALSHI_KEY_ID in .env")


def load_tickers() -> list[str]:
    cfg = json.loads(CONFIG.read_text())
    tickers = cfg.get("tickers", [])
    if not tickers:
        raise SystemExit("config/kalshi_universe.json has no tickers")
    return tickers


async def run_once(tickers, writer, pk, key_id):
    headers = auth_headers(pk, key_id, "GET", WS_PATH)
    async with websockets.connect(WS_URL, additional_headers=headers, ping_interval=10, ping_timeout=10) as ws:
        sub = {"id": 1, "cmd": "subscribe", "params": {"channels": ["orderbook_delta"], "market_tickers": tickers}}
        await ws.send(json.dumps(sub))
        log.info("subscribed", n_markets=len(tickers))
        last_beat = 0.0
        async for message in ws:
            writer.write(message)
            now = asyncio.get_event_loop().time()
            if now - last_beat > 15:
                HEARTBEAT.touch()
                last_beat = now
            if writer.count % 2000 == 0:
                log.info("progress", messages=writer.count)


async def main():
    tickers = load_tickers()
    pk = load_private_key()
    key_id = load_key_id()
    writer = DailyWriter(str(DATA_DIR), "kalshi")
    backoff = 1.0
    try:
        while True:
            try:
                await run_once(tickers, writer, pk, key_id)
                log.warning("stream_ended")
                backoff = 1.0
            except Exception as exc:
                log.error("stream_error", error=str(exc), backoff=backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
    finally:
        writer.close()


if __name__ == "__main__":
    structlog.configure(processors=[structlog.processors.JSONRenderer()])
    asyncio.run(main())
