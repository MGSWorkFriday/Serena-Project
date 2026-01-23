# server/session.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from pathlib import Path
from typing import Any, Dict, Optional, List

# --- Constanten & Paden ---
DEFAULT_BUFFER_SIZE = 2000

BASE_DIR = Path(__file__).resolve().parent.parent 
PARAM_FILE = BASE_DIR / "resp_rr_param_sets.json"
TECH_FILE = BASE_DIR / "server/techniques.json"

log = logging.getLogger("session")

class DeviceSession:
    def __init__(self, device_id: str):
        self.device_id = device_id
        
        # Buffer configuratie
        self.buffer_size = DEFAULT_BUFFER_SIZE
        self.ecg_buffer: deque = deque(maxlen=self.buffer_size)
        
        # Opslag voor recente geschiedenis
        self.history: deque = deque(maxlen=1000)
        self.last_emitted_ts: Optional[int] = None
        
        # Adem status
        self.current_target_rr: float = 0.0
        self.current_breath_cycle: Optional[dict] = None
        
        # Huidige techniek naam
        self.current_technique: Optional[str] = None
        
        # --- Dynamisch Parameter Beheer ---
        raw_params = self._load_json(PARAM_FILE)
        self.param_registry = {}
        
        if isinstance(raw_params, list):
            for p in raw_params:
                v_key = p.get("version")
                if v_key: self.param_registry[v_key] = p
        elif isinstance(raw_params, dict):
            self.param_registry = raw_params
        
        self.default_version = "v1_default" 
        if self.default_version not in self.param_registry and self.param_registry:
            first_key = next(iter(self.param_registry))
            self.default_version = first_key

        self.active_params: Dict[str, Any] = self.param_registry.get(self.default_version, {})
        self.active_version_name = self.default_version

        self._apply_buffer_size_from_params()
        self.listeners: List[asyncio.Queue] = []

    def _load_json(self, path: Path) -> Any:
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            log.error(f"Fout bij laden {path.name}: {e}")
            return {}

    def _apply_buffer_size_from_params(self):
        new_size = self.active_params.get("BUFFER_SIZE", DEFAULT_BUFFER_SIZE)
        if new_size != self.ecg_buffer.maxlen:
            log.info(f"[{self.device_id}] Buffer resize: {self.ecg_buffer.maxlen} -> {new_size}")
            self.ecg_buffer = deque(self.ecg_buffer, maxlen=new_size)
            self.buffer_size = new_size

    def activate_technique(self, tech_name: str):
        """Wordt aangeroepen vanuit utils.py bij BreathTarget update."""
        if not tech_name:
            return

        self.current_technique = tech_name

        tech_registry = self._load_json(TECH_FILE)
        tech_info = tech_registry.get(tech_name)
        if not tech_info:
            return

        version = tech_info.get("param_version")
        target_version = version if version else self.default_version
        
        if target_version == self.active_version_name:
            return 

        if target_version in self.param_registry:
            self.active_params = self.param_registry[target_version]
            self.active_version_name = target_version
            log.info(f"[{self.device_id}] Techniek '{tech_name}' activeert params: {target_version}")
            self._apply_buffer_size_from_params()
        else:
            log.warning(f"[{self.device_id}] Parameter versie '{target_version}' niet gevonden in registry.")

    def reset_params(self):
        """Wordt aangeroepen als de oefening stopt."""
        self.current_technique = None 

        if self.active_version_name != self.default_version:
            log.info(f"[{self.device_id}] Reset naar default parameters ({self.default_version})")
            self.active_params = self.param_registry.get(self.default_version, {})
            self.active_version_name = self.default_version
            self._apply_buffer_size_from_params()

    async def broadcast(self, data: dict):
        self.history.append(data)
        if not self.listeners: return
        to_remove = []
        for q in self.listeners:
            try: q.put_nowait(data)
            except asyncio.QueueFull: to_remove.append(q)
            except Exception: to_remove.append(q)
        for q in to_remove:
            if q in self.listeners: self.listeners.remove(q)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, DeviceSession] = {}

    def get_session(self, device_id: str) -> DeviceSession:
        if device_id not in self.sessions:
            log.info(f"Nieuwe sessie aangemaakt voor ID: {device_id}")
            self.sessions[device_id] = DeviceSession(device_id)
        return self.sessions[device_id]

    async def distribute_data(self, data: dict):
        dev_id = data.get("device_id", "UNKNOWN")
        if dev_id != "UNKNOWN":
            session = self.get_session(dev_id)
            await session.broadcast(data)
        global_session = self.get_session("UNKNOWN")
        await global_session.broadcast(data)

    async def subscribe(self, device_id: str):
        session = self.get_session(device_id)
        q = asyncio.Queue(maxsize=100)
        session.listeners.append(q)
        try:
            while True:
                data = await q.get()
                yield data
        except asyncio.CancelledError:
            if q in session.listeners:
                session.listeners.remove(q)

manager = SessionManager()