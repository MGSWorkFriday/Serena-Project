# -*- coding: utf-8 -*-
from urllib import request, parse
import json
import os
from sensor_config import SERVER_BASE

def call_health():
    """Check of de server leeft."""
    try:
        with request.urlopen(f"{SERVER_BASE}/healthz", timeout=2) as r:
            return True, f"[ok] Health: {r.read().decode()}"
    except Exception as e:
        return False, f"[fout] Health: {e}"

def call_rotate(file_name=None):
    """Roept de rotate endpoint aan."""
    base = f"{SERVER_BASE}/rotate"
    url = f"{base}?{parse.urlencode({'name': os.path.basename(file_name)})}" if file_name else base
    
    try:
        with request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode())
            return True, f"[ok] Rotate naar: {data.get('file')}"
    except Exception as e:
        return False, f"[fout] Rotate mislukt: {e}"
