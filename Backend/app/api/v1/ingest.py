# -*- coding: utf-8 -*-
"""Data ingestion endpoint"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException

from app.database import get_database
from app.models.signal import RecordIngest, IngestResponse
from app.schemas.signal import SignalRecord
from app.services.stream_manager import stream_manager
from app.services.signal_processor import SignalProcessor
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

# Global signal processor
signal_processor = SignalProcessor()


def parse_timestamp(ts: any) -> Optional[int]:
    """Parse timestamp to milliseconds"""
    if ts is None:
        return int(datetime.now().timestamp() * 1000)
    
    try:
        ts_int = int(ts)
        # Convert nanoseconds to milliseconds
        if ts_int > 10_000_000_000_000:
            return ts_int // 1_000_000
        # Convert seconds to milliseconds
        if 1_000_000_000 < ts_int < 10_000_000_000:
            return ts_int * 1000
        # Already milliseconds
        if 1_000_000_000_000 < ts_int < 10_000_000_000_000:
            return ts_int // 1000
        if 1_000_000_000_000 <= ts_int <= 10_000_000_000_000:
            return ts_int
        # Assume milliseconds if in reasonable range
        if 1_000_000_000 < ts_int < 10_000_000_000_000:
            return ts_int
        return int(datetime.now().timestamp() * 1000)
    except (ValueError, TypeError):
        return int(datetime.now().timestamp() * 1000)


def parse_dt_from_ts(ts: int) -> str:
    """Convert timestamp (ms) to dt string format"""
    dt = datetime.fromtimestamp(ts / 1000.0)
    ms = ts % 1000
    return dt.strftime("%d-%m-%Y %H:%M:%S") + f":{ms:03d}"


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: Request):
    """Ingest sensor data (NDJSON or JSON array)"""
    print("=" * 50, flush=True)
    print("[INGEST] Request received!", flush=True)
    print("=" * 50, flush=True)
    db = await get_database()
    
    ctype = request.headers.get("content-type", "").lower()
    print(f"[INGEST] Content-Type: '{ctype}'", flush=True)
    accepted = 0
    active_session_id: Optional[str] = None
    
    try:
        records_to_insert: List[dict] = []
        
        if "application/x-ndjson" in ctype:
            # NDJSON format
            print("[INGEST] Processing as NDJSON", flush=True)
            buf = b""
            async for chunk in request.stream():
                if not chunk:
                    continue
                buf += chunk
                print(f"[INGEST] Received chunk, buf size: {len(buf)}", flush=True)
                while True:
                    nl = buf.find(b"\n")
                    if nl < 0:
                        print(f"[INGEST] No newline found in buf, waiting for more data", flush=True)
                        break
                    line = buf[:nl].strip()
                    buf = buf[nl + 1:]
                    if not line:
                        continue
                    
                    print(f"[INGEST] Got line: {line[:100]}...", flush=True)
                    try:
                        data = json.loads(line)
                        print(f"[INGEST] Parsed JSON, signal={data.get('signal')}", flush=True)
                        payload = [data] if isinstance(data, dict) else (data if isinstance(data, list) else None)
                        if payload:
                            for item in payload:
                                rec = RecordIngest(**item)
                                session_id, signals = await process_record(rec, db)
                                if session_id:
                                    active_session_id = session_id
                                records_to_insert.extend(signals)
                                accepted += 1
                    except json.JSONDecodeError as e:
                        print(f"[INGEST] JSON decode error: {e}", flush=True)
                        continue
                    except Exception as e:
                        print(f"[INGEST] Error processing: {e}", flush=True)
                        continue
            # Process any remaining data in buffer (no trailing newline)
            if buf.strip():
                print(f"[INGEST] Processing remaining buffer: {len(buf)} bytes", flush=True)
                try:
                    data = json.loads(buf)
                    print(f"[INGEST] Parsed remaining JSON, signal={data.get('signal') if isinstance(data, dict) else 'array'}", flush=True)
                    payload = [data] if isinstance(data, dict) else (data if isinstance(data, list) else None)
                    if payload:
                        for item in payload:
                            rec = RecordIngest(**item)
                            session_id, signals = await process_record(rec, db)
                            if session_id:
                                active_session_id = session_id
                            records_to_insert.extend(signals)
                            accepted += 1
                except json.JSONDecodeError as e:
                    print(f"[INGEST] Final buffer JSON decode error: {e}", flush=True)
                except Exception as e:
                    print(f"[INGEST] Final buffer error: {e}", flush=True)
            print(f"[INGEST] NDJSON done, accepted: {accepted}", flush=True)
        else:
            # JSON format
            payload = await request.json()
            print(f"[INGEST] Payload type: {type(payload).__name__}, length: {len(payload) if isinstance(payload, list) else 'N/A'}", flush=True)
            if isinstance(payload, dict):
                print(f"[INGEST] Single record, signal={payload.get('signal')}", flush=True)
                rec = RecordIngest(**payload)
                session_id, signals = await process_record(rec, db)
                if session_id:
                    active_session_id = session_id
                records_to_insert.extend(signals)
                accepted += 1
            elif isinstance(payload, list):
                print(f"[INGEST] Array of {len(payload)} records", flush=True)
                for item in payload:
                    print(f"[INGEST] Processing item, signal={item.get('signal')}", flush=True)
                    rec = RecordIngest(**item)
                    session_id, signals = await process_record(rec, db)
                    if session_id:
                        active_session_id = session_id
                    records_to_insert.extend(signals)
                    accepted += 1
            else:
                print(f"[INGEST] Unknown payload type: {type(payload)}", flush=True)
        
        # Insert all records
        if records_to_insert:
            await db.signals.insert_many(records_to_insert, ordered=False)
        
        return IngestResponse(accepted=accepted, session_id=active_session_id)
    
    except Exception as e:
        logger.exception("Error in /ingest")
        raise HTTPException(status_code=500, detail=str(e))


async def process_record(rec: RecordIngest, db) -> tuple[Optional[str], List[dict]]:
    """Process a single record and return (session_id, signals_to_insert)"""
    device_id = rec.device_id or "UNKNOWN"
    print(f"[process_record] signal={rec.signal}, device={device_id}, samples={len(rec.samples) if rec.samples else 0}", flush=True)
    
    # Parse timestamp
    ts = parse_timestamp(rec.ts)
    dt = parse_dt_from_ts(ts)
    
    # Get or create active session
    session_doc = await db.sessions.find_one({
        "device_id": device_id,
        "status": "active"
    })
    session_id = session_doc["session_id"] if session_doc else None
    
    if rec.signal == "ecg":
        if session_doc:
            print(f"[ingest] Found active session {session_id} for device {device_id}", flush=True)
        else:
            print(f"[ingest] !! NO ACTIVE SESSION for device_id={device_id} !!", flush=True)
    
    # Handle BreathTarget - update/create session
    if rec.signal == "BreathTarget":
        target_rr = getattr(rec, "TargetRR", 0) or 0
        technique_name = getattr(rec, "technique", None)
        
        if target_rr == 0:
            # End session
            if session_doc:
                await db.sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "ended_at": datetime.utcnow(),
                        "status": "completed"
                    }}
                )
                session_id = None
        elif target_rr > 0:
            # Start or update session
            if session_doc:
                await db.sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "technique_name": technique_name,
                        "target_rr": target_rr,
                    }}
                )
            else:
                from app.schemas.session import Session
                session = Session(
                    device_id=device_id,
                    technique_name=technique_name,
                    target_rr=target_rr,
                    started_at=datetime.fromtimestamp(ts / 1000.0),
                )
                result = await db.sessions.insert_one(session.to_dict())
                session_id = session.session_id
    
    # Create signal record
    signal_dict = rec.model_dump()
    signal_record = SignalRecord(
        device_id=device_id,
        signal=rec.signal,
        ts=ts,
        dt=dt,
        session_id=session_id,
        samples=signal_dict.get("samples"),
        bpm=signal_dict.get("bpm"),
        estRR=signal_dict.get("estRR"),
        tijd=signal_dict.get("tijd"),
        inhale=signal_dict.get("inhale"),
        exhale=signal_dict.get("exhale"),
        text=signal_dict.get("text"),
        audio_text=signal_dict.get("audio_text"),
        color=signal_dict.get("color"),
        target=signal_dict.get("target"),
        actual=signal_dict.get("actual"),
        TargetRR=signal_dict.get("TargetRR"),
        breath_cycle=signal_dict.get("breath_cycle"),
        technique=signal_dict.get("technique"),
        active_param_version=signal_dict.get("active_param_version"),
    )
    
    signal_dict = signal_record.to_dict()
    
    # Broadcast to subscribers
    await stream_manager.broadcast(signal_dict)
    
    # Process ECG signals for RR estimation (async, non-blocking)
    # Note: This runs in background, errors are logged but don't block ingest
    if rec.signal == "ecg":
        if session_id:
            print(f"[ECG] Processing ecg for session {session_id}, device {device_id}", flush=True)
            try:
                asyncio.create_task(
                    signal_processor.process_ecg_signal(signal_dict, session_id, db)
                )
            except Exception as e:
                print(f"[ECG] Failed to start processing task: {e}", flush=True)
        else:
            print(f"[ECG] !! NO SESSION - ECG NOT PROCESSED for device {device_id} !!", flush=True)
    
    return session_id, [signal_dict]
