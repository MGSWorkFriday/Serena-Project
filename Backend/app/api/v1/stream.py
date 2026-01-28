# -*- coding: utf-8 -*-
"""Real-time streaming endpoint (SSE)"""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json

from app.services.stream_manager import stream_manager

router = APIRouter()


@router.get("/stream")
async def stream_signals(
    signals: str = Query("hr_est", description="Comma-separated signal types, or 'all'"),
    device_id: str = Query("UNKNOWN", description="Device ID to subscribe to"),
):
    """Server-Sent Events stream for real-time signal data"""
    
    want_signals = set(s.strip() for s in signals.split(",") if s.strip())
    
    async def event_generator():
        """Generate SSE events"""
        try:
            async for data in stream_manager.subscribe(device_id):
                signal_type = data.get("signal")
                
                # Filter by signal type
                if want_signals and "all" not in want_signals and signal_type not in want_signals:
                    continue
                
                # Format as SSE
                event_data = json.dumps(data, ensure_ascii=False)
                yield f"data: {event_data}\n\n"
        except Exception as e:
            # Send error event
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
