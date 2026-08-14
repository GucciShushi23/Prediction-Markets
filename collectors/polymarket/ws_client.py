"""Polymarket CLOB market-channel collector.

Writes every raw message plus a receive timestamp. Parses nothing.
Reconnects with exponential backoff. Touches a heartbeat file for monitoring.

Run:  py -m uv run python collectors/polymarket/ws_client.py
"""
import asyncio
import json
import sys
from pathlib import Path

import structlog
import websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.writer import DailyWriter  # noqa: E402

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
CONFIG = Path(__file__).resolve().parents[2] / "config" / "universe.json"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
HEARTBEAT = Path("polymarket_collector.heartbeat")

log = structlog.get_logger()


def load_token_ids() -> list[str]:
    cfg = json.loads(CONFIG.read_text())
    ids = cfg["polymarket"]["token_ids"]
    if not ids:
        raise SystemExit("config/universe.json has no polymarket token_ids")
    return ids


async def run_once(token_ids: list[str], writer: DailyWriter) -> None:
    async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as ws:
        await ws.send(json.dumps({
            "type": "market",
            "assets_ids": token_ids,
            "custom_feature_enabled": True,
        }))
        log.info("subscribed", n_markets=len(token_ids))

        last_beat = 0.0
        async for message in ws:
            writer.write(message)
            now = asyncio.get_event_loop().time()
            if now - last_beat > 15:
                HEARTBEAT.touch()
                last_beat = now
            if writer.count % 5000 == 0:
                log.info("progress", messages=writer.count)


async def main() -> None:
    token_ids = load_token_ids()
    writer = DailyWriter(str(DATA_DIR), "polymarket")
    backoff = 1.0
    try:
        while True:
            try:
                await run_once(token_ids, writer)
                log.warning("stream_ended_cleanly")
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