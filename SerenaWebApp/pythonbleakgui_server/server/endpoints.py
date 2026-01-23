# -*- coding: utf-8 -*-
# server/endpoints.py
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator, List

from fastapi import HTTPException, Request, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

# 1. Correcte import van session manager
from .session import manager

from .models import IngestResponse, Record
from .utils import (
    _append_lines, _derive_resp_lines, _today_file, 
    dumps, log, WEB_DIR, 
    reset_runtime_state, rotate_logfile, 
    BULK_MINIMAL_LOG, BULK_SIGNAL_WHITELIST,
    _to_epoch_ms,
    enrich_with_dt # <--- NIEUWE IMPORT
)
from pathlib import Path  

async def healthz(): return {"status": "ok", "now": datetime.utcnow().isoformat() + "Z"}
async def reset(request: Request): return {"status": "ok"}
async def rotate(request: Request): return {"status": "ok"}
async def rotate_get(request: Request): return await rotate(request)

async def ingest(request: Request):
    ctype = request.headers.get("content-type", "").lower()
    lines_to_write: List[str] = []
    accepted = 0

    # Helper: verwerk record
    async def handle_record(rec: Record, bulk_mode: bool, device_id: str = None):
        nonlocal accepted, lines_to_write
        rec_dict = rec.dict()
        
        # ID Zekerheid
        if device_id: rec_dict["device_id"] = device_id
        elif "device_id" not in rec_dict: rec_dict["device_id"] = "UNKNOWN"
        final_dev_id = rec_dict["device_id"]

        # 2. HAAL DE JUISTE SESSIE OP
        session = manager.get_session(final_dev_id)

        # 3. GEEF SESSIE MEE AAN DE REKENFUNCTIE
        # utils.py zorgt nu zelf voor de 'dt' tag in deze derived lines
        derived_lines = _derive_resp_lines(rec_dict, session)

        # Logging naar disk (Nu met BULK_MINIMAL_LOG=False schrijft hij ALLES)
        if bulk_mode and BULK_MINIMAL_LOG:
            for ln in derived_lines:
                try:
                    obj = json.loads(ln)
                except Exception: continue
                sig = obj.get("signal")
                if (not BULK_SIGNAL_WHITELIST) or (sig in BULK_SIGNAL_WHITELIST):
                    lines_to_write.append(ln)
        else:
            # We schrijven de RUWE data (rec_dict).
            # HIER VOEGEN WE DE DATUM TOE AAN HET RUWE RECORD:
            lines_to_write.append(dumps(enrich_with_dt(rec_dict)))
            
            # De derived lines hebben de dt al gekregen in _derive_resp_lines
            lines_to_write.extend(derived_lines)

        # Broadcast naar browsers (Live View)
        # Eerst het originele ECG packet
        await manager.distribute_data(rec_dict) 
        
        # Dan de afgeleide data (RR, BPM, Guidance, etc.)
        for ln in derived_lines:
            try:
                d_obj = json.loads(ln)
                if "device_id" not in d_obj: d_obj["device_id"] = final_dev_id
                await manager.distribute_data(d_obj)
            except Exception: pass
        
        accepted += 1
        return final_dev_id # Geef ID terug voor map-bepaling

    # We houden het laatste device ID bij voor logging folder
    final_dev_id_for_log = "UNKNOWN"

    try:
        if "application/x-ndjson" in ctype:
            buf = b""
            async for chunk in request.stream():
                if not chunk: continue
                buf += chunk
                while True:
                    nl = buf.find(b"\n")
                    if nl < 0: break
                    line = buf[:nl].strip(); buf = buf[nl + 1:]
                    if not line: continue
                    data = json.loads(line)
                    payload = [data] if isinstance(data, dict) else (data if isinstance(data, list) else None)
                    if payload:
                        for item in payload:
                            rec = Record(**item)
                            final_dev_id_for_log = await handle_record(rec, True, item.get("device_id"))
        else:
            payload = await request.json()
            if isinstance(payload, dict):
                rec = Record(**payload)
                final_dev_id_for_log = await handle_record(rec, False, payload.get("device_id"))
            elif isinstance(payload, list):
                for item in payload:
                    rec = Record(**item)
                    final_dev_id_for_log = await handle_record(rec, True, item.get("device_id"))

        # AANGEPAST: Geef het device ID mee aan _append_lines voor de juiste submap
        if lines_to_write:
            file_path = await _append_lines(lines_to_write, device_id=final_dev_id_for_log)
        else:
            file_path = str(_today_file(device_id=final_dev_id_for_log).resolve())
            
        return IngestResponse(accepted=accepted, file=file_path)

    except Exception as e:
        log.exception("Fout in /ingest")
        raise HTTPException(status_code=500, detail=str(e))

async def recent(signal: str = "hr_est", limit: int = 300, device: str = Query(None)):
    target_device = device or "UNKNOWN"
    session = manager.get_session(target_device)
    history_items = list(session.history)
    out: List[dict] = []
    
    for obj in reversed(history_items):
        if obj.get("signal") != signal: continue
        ts = _to_epoch_ms(obj.get("ts")) or _to_epoch_ms(obj.get("ts_ms")) or int(datetime.now().timestamp() * 1000)
        
        if signal in ("hr_est", "hr_derived"): out.append({"ts": ts, "bpm": obj.get("bpm")})
        else: c = obj.copy(); c["ts"] = ts; out.append(c)
        if len(out) >= limit: break
            
    out.sort(key=lambda x: x.get("ts", 0))
    return {"signal": signal, "count": len(out), "items": out}

async def stream(signals: str = "hr_est", device: str = Query(None)):
    want = set(s.strip() for s in signals.split(",") if s.strip())
    target_device = device or "UNKNOWN"

    async def event_gen() -> AsyncIterator[bytes]:
        async for data in manager.subscribe(target_device):
            sig = data.get("signal")
            
            # Filter logica
            if want and "all" not in want and sig not in want: 
                continue
            
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")

    return StreamingResponse(event_gen(), media_type="text/event-stream")

async def ui():
    index = WEB_DIR / "index.html"
    if not index.exists(): return HTMLResponse("<h3>UI not found.</h3>", status_code=200)
    return FileResponse(index)