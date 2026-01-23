# -*- coding: utf-8 -*-
"""
ECG Data Replay Tool — streaming (timestamp-paced) + bulk
- Streaming: sends records one-by-one and SLEEPS between posts according to ts deltas.
- Bulk: sends all (or in batches) as NDJSON or JSON array.
"""

from pathlib import Path
import argparse
import asyncio
import aiohttp
import json
from typing import Iterable, List, Optional, Set, Dict, Any


def load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                yield obj
            except Exception as e:
                print(f"[WARN] Skip malformed line {lineno}: {e}")


class ECGReplayer:
    def __init__(
        self,
        file_path: str,
        url: str,
        speed: float = 1.0,
        signals: Optional[Set[str]] = None,
        loop: bool = False,
        ts_unit: str = "ms",
        bulk: bool = False,
        batch_size: int = 0,
        bulk_format: str = "ndjson",
        verbose: bool = False,
    ):
        self.file_path = Path(file_path)
        self.url = url
        self.speed = max(0.001, float(speed))  # avoid div-by-zero
        self.signals = signals or {"ecg"}
        self.loop = loop
        self.ts_unit = ts_unit  # "ms" or "s"
        self.bulk = bulk
        self.batch_size = int(batch_size) if batch_size else 0
        self.bulk_format = bulk_format  # "ndjson" or "json"
        self.verbose = verbose
        self.session: Optional[aiohttp.ClientSession] = None

        self.last_sent_ts: Optional[int] = None

    def iter_records(self) -> Iterable[Dict[str, Any]]:
        for obj in load_jsonl(self.file_path):
            sig = obj.get("signal")
            if self.signals != {"*"} and sig not in self.signals:
                continue
            if "ts" not in obj:
                continue
            yield obj

    async def send_record(self, record: Dict[str, Any]) -> None:
        assert self.session is not None, "HTTP session not initialized"
        try:
            async with self.session.post(self.url, json=record) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    print(f"[HTTP {resp.status}] {text[:300]}")
        except Exception as e:
            print(f"[ERROR] POST single failed: {e}")

    async def send_batch(self, batch: List[Dict[str, Any]]) -> None:
        assert self.session is not None, "HTTP session not initialized"
        try:
            if self.bulk_format == "ndjson":
                payload = "\\n".join(json.dumps(r, ensure_ascii=False) for r in batch) + "\\n"
                headers = {"Content-Type": "application/x-ndjson"}
                async with self.session.post(self.url, data=payload.encode("utf-8"), headers=headers) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        print(f"[HTTP {resp.status}] {text[:300]}")
            else:  # json array
                headers = {"Content-Type": "application/json"}
                async with self.session.post(self.url, json=batch, headers=headers) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        print(f"[HTTP {resp.status}] {text[:300]}")
        except Exception as e:
            print(f"[ERROR] POST batch failed: {e}")

    def _sleep_seconds_from_delta(self, delta_ts: int) -> float:
        if self.ts_unit == "s":
            dt_seconds = float(delta_ts)
        else:  # "ms"
            dt_seconds = float(delta_ts) / 1000.0
        return max(0.0, dt_seconds / self.speed)

    async def replay_stream(self) -> None:
        print("=" * 60)
        print(f"Streaming replay (signals={','.join(sorted(self.signals))}, speed={self.speed}x, ts_unit={self.ts_unit})")
        print("=" * 60)

        self.last_sent_ts = None

        while True:
            prev_ts_for_sleep: Optional[int] = None
            sent = 0
            for record in self.iter_records():
                ts = record.get("ts")
                if ts is None:
                    continue
                if self.last_sent_ts is not None and ts <= self.last_sent_ts:
                    if self.verbose:
                        print(f"[SKIP] Non-increasing ts (last={self.last_sent_ts}, current={ts})")
                    continue

                if prev_ts_for_sleep is not None:
                    delta = ts - prev_ts_for_sleep
                    sleep_s = self._sleep_seconds_from_delta(delta)
                    if sleep_s > 0:
                        await asyncio.sleep(sleep_s)

                await self.send_record(record)
                sent += 1
                if self.verbose and sent % 100 == 0:
                    print(f"[INFO] Streamed {sent} records...")

                prev_ts_for_sleep = ts
                self.last_sent_ts = ts

            print(f"Finished one pass: {self.file_path.name} (sent={sent})")
            if not self.loop:
                break
            print("Looping...")

    async def replay_bulk(self) -> None:
        print("=" * 60)
        mode = f"bulk-{self.bulk_format}"
        print(f"Bulk replay ({mode}), batch_size={self.batch_size or 'ALL'}, signals={','.join(sorted(self.signals))}")
        print("=" * 60)

        collected: List[Dict[str, Any]] = []
        last_ts: Optional[int] = None
        for record in self.iter_records():
            ts = record.get("ts")
            if ts is None:
                continue
            if last_ts is not None and ts <= last_ts:
                if self.verbose:
                    print(f"[SKIP] Non-increasing ts (last={last_ts}, current={ts})")
                continue
            collected.append(record)
            last_ts = ts

        print(f"[INFO] Collected {len(collected)} records for bulk send.")
        if not collected:
            print("No records to send.")
            return

        if self.batch_size and self.batch_size > 0:
            for i in range(0, len(collected), self.batch_size):
                print(f"[INFO] Sending batch {i//self.batch_size + 1} "
                      f"({i}..{min(i+self.batch_size, len(collected)) - 1})")
                await self.send_batch(collected[i : i + self.batch_size])
        else:
            print("[INFO] Sending single bulk request...")
            await self.send_batch(collected)

        print(f"Bulk done: sent {len(collected)} records.")

    async def run(self) -> None:
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(raise_for_status=False, timeout=timeout) as session:
            self.session = session
            if self.bulk:
                await self.replay_bulk()
            else:
                await self.replay_stream()
            self.session = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ECG replayer with timestamp-paced streaming and bulk modes.")
    p.add_argument("--file", required=True, help="Path to source JSONL file")
    p.add_argument("--url", required=True, help="Target ingest URL")
    p.add_argument("--signals", default="ecg", help="Comma-separated list of signals (default: ecg). Use * for all.")
    p.add_argument("--loop", action="store_true", help="Repeat the file indefinitely (stream mode only)")
    p.add_argument("--speed", type=float, default=1.0, help="Playback speed factor (1.0=realtime, 2.0=2x faster, etc.)")
    p.add_argument("--ts-unit", choices=["ms", "s"], default="ms", help="Units of the 'ts' field (default: ms)")
    p.add_argument("--verbose", action="store_true", help="Verbose progress logs")
    # bulk options
    p.add_argument("--bulk", action="store_true", help="Enable bulk mode (send all or batches)")
    p.add_argument("--batch-size", type=int, default=0, help="Batch size for bulk mode (0 = all in one request)")
    p.add_argument("--format", dest="bulk_format", choices=["ndjson", "json"], default="ndjson", help="Bulk payload format")
    return p.parse_args()


def main():
    args = parse_args()
    signals = set([s.strip() for s in args.signals.split(",") if s.strip()]) or {"ecg"}
    runner = ECGReplayer(
        file_path=args.file,
        url=args.url,
        speed=args.speed,
        signals=signals,
        loop=args.loop,
        ts_unit=args.ts_unit,
        bulk=args.bulk,
        batch_size=args.batch_size,
        bulk_format=args.bulk_format,
        verbose=args.verbose,
    )
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
