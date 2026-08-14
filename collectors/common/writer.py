"""Append-only daily JSONL writer. Raw in, no parsing."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path


class DailyWriter:
    def __init__(self, base_dir: str, venue: str):
        self.base = Path(base_dir)
        self.venue = venue
        self._fh = None
        self._day = None
        self.count = 0

    def _path_for(self, day: str) -> Path:
        d = self.base / self.venue / day
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{self.venue}-{day}.jsonl"

    def write(self, payload: str) -> None:
        now = datetime.now(timezone.utc)
        day = now.strftime("%Y-%m-%d")
        if day != self._day:
            if self._fh:
                self._fh.close()
            self._fh = open(self._path_for(day), "a", buffering=1)
            self._day = day
        record = {
            "recv_ts": time.time_ns() // 1000,   # microseconds
            "venue": self.venue,
            "raw": payload,
        }
        self._fh.write(json.dumps(record) + "\n")
        self.count += 1

    def close(self) -> None:
        if self._fh:
            self._fh.close()