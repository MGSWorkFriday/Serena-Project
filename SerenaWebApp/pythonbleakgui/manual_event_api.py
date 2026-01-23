# manual_event_api.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import requests
import time
import threading
from typing import Tuple, Any

def send_inhale_marker(ingest_url: str) -> Tuple[bool, str]:
    """
    Constructs and sends an 'inhale' marker to the ingest endpoint.

    Args:
        ingest_url: The full URL to the /ingest endpoint (e.g., http://localhost:8000/ingest).

    Returns:
        A tuple (success: bool, message: str)
    """
    # Gebruik de huidige epoch tijd in milliseconden
    ts_ms = int(time.time() * 1000)

    # De payload volgens het afgesproken formaat
    payload = {
        "signal": "marker",
        "event": "inhale",
        "ts": ts_ms
    }

    try:
        # Verstuur de data met de ingest URL van de dashboard-config
        response = requests.post(ingest_url, json=payload, timeout=5)
        response.raise_for_status() # Gooi een exception voor 4xx/5xx

        try:
            # Probeer de JSON response te parsen
            result = response.json()
            message = f"[INFO] Inhale marker verzonden ({result.get('accepted', 0)} geaccepteerd)."
            return True, message
        except Exception:
            # Bijvoorbeeld als de server alleen 'ok' terugstuurt zonder JSON body
            return True, f"[INFO] Inhale marker verzonden (Status {response.status_code})."

    except requests.exceptions.RequestException as e:
        # Fout bij het bereiken van de server (verbinding, timeout, DNS, etc.)
        return False, f"[FOUT] Versturen marker mislukt naar {ingest_url}: {e}"