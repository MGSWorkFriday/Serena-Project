# -*- coding: utf-8 -*-
import os
import json
import sys

SERVER_BASE = "http://localhost:8000"

def get_base_dir():
    """Geeft de map terug waar het huidige script draait."""
    return os.path.dirname(os.path.abspath(__file__))

def get_server_dir():
    """Zoekt de map van de pythonbleakgui_server."""
    base = get_base_dir()
    return os.path.abspath(os.path.join(base, "..", "pythonbleakgui_server"))

def load_resp_versions():
    """Laadt de beschikbare versies uit resp_rr_param_sets.json."""
    server_dir = get_server_dir()
    json_path = os.path.join(server_dir, "resp_rr_param_sets.json")
    
    if not os.path.exists(json_path):
        return []
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        versions = []
        if isinstance(data, dict):
            versions = list(data.keys())
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    versions.append(str(item.get("version", item.get("name", ""))))
        return sorted([v for v in versions if v])
    except Exception:
        return []

def get_default_log_folder():
    """Probeert slim de log folder te raden."""
    # 1. Server logs
    candidate = os.path.join(get_server_dir(), "logs")
    if os.path.exists(candidate) and os.path.isdir(candidate):
        return candidate
        
    # 2. Lokale logs
    local = os.path.join(get_base_dir(), "logs")
    if os.path.exists(local):
        return local
        
    return ""