# network.py
import asyncio
import aiohttp

class IngestClient:
    """
    Simpele batched HTTP-ingest:
    - `add(record)` stopt record in batch
    - background task pusht elke `batch_ms` of zodra `batch_size` bereikt is
    """
    def __init__(self, url: str, batch_ms: int = 250, batch_size: int = 200, log_fn=None):
        self.url = url
        self.batch_ms = max(50, int(batch_ms))
        self.batch_size = max(1, int(batch_size))
        self._session = None
        self._task = None
        self._closed = False
        self._batch = []
        self._last_flush = 0.0
        self._log = log_fn or (lambda s: None)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            raise_for_status=False,
            timeout=aiohttp.ClientTimeout(total=10)
        )
        self._closed = False
        self._last_flush = asyncio.get_event_loop().time()
        self._task = asyncio.create_task(self._flush_loop())
        self._log(f"[INGEST] Actief: {self.url} (batch {self.batch_size} / {self.batch_ms}ms)")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._closed = True
        if self._task:
            await self._task
        if self._session:
            await self._session.close()
        self._log("[INGEST] Gesloten.")

    async def add(self, rec: dict):
        self._batch.append(rec)
        now = asyncio.get_event_loop().time()
        if len(self._batch) >= self.batch_size or (now - self._last_flush) >= (self.batch_ms/1000.0):
            await self._send_batch()

    async def _flush_loop(self):
        while not self._closed:
            await asyncio.sleep(self.batch_ms/1000.0)
            if self._batch:
                await self._send_batch()
        if self._batch:
            await self._send_batch()

    async def _send_batch(self):
        assert self._session is not None
        batch = self._batch
        self._batch = []
        self._last_flush = asyncio.get_event_loop().time()
        try:
            async with self._session.post(self.url, json=batch) as r:
                if r.status >= 300:
                    txt = await r.text()
                    self._log(f"[INGEST ERR] {r.status}: {txt[:300]}")
        except Exception as e:
            self._log(f"[INGEST ERR] {e}")