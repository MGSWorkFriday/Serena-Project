# -*- coding: utf-8 -*-
"""Stream manager for real-time data broadcasting"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, Set, AsyncIterator
from collections import defaultdict

logger = logging.getLogger(__name__)


class StreamManager:
    """Manages real-time data streams using in-memory pub/sub"""
    
    def __init__(self):
        # Map: device_id -> set of queues
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
    
    async def subscribe(self, device_id: str) -> AsyncIterator[dict]:
        """Subscribe to data stream for a device"""
        q = asyncio.Queue(maxsize=100)
        
        async with self._lock:
            self._subscribers[device_id].add(q)
        
        try:
            while True:
                data = await q.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                if q in self._subscribers[device_id]:
                    self._subscribers[device_id].remove(q)
    
    async def broadcast(self, data: dict):
        """Broadcast data to subscribers"""
        device_id = data.get("device_id", "UNKNOWN")
        
        # Broadcast to device-specific subscribers
        async with self._lock:
            queues = list(self._subscribers.get(device_id, set()))
            # Also broadcast to UNKNOWN subscribers
            if device_id != "UNKNOWN":
                queues.extend(self._subscribers.get("UNKNOWN", set()))
        
        if not queues:
            return
        
        # Send to all subscribers (non-blocking)
        for queue in queues:
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                # Remove full queue
                async with self._lock:
                    if queue in self._subscribers[device_id]:
                        self._subscribers[device_id].remove(queue)
            except Exception as e:
                logger.warning(f"Error broadcasting to subscriber: {e}")
                async with self._lock:
                    if device_id in self._subscribers:
                        self._subscribers[device_id].discard(queue)


# Global stream manager instance
stream_manager = StreamManager()
