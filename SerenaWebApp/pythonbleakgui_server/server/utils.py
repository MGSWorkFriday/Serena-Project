# server/utils.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union
from collections import deque
from dataclasses import asdict

import aiofiles
import numpy as np

# --- CONFIGURATIE ---
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# --- IMPORTS ---
try:
    from resp_rr_estimator import estimate_from_records
except ImportError as e:
    logging.error(f"KRITIEK: Kan 'resp_rr_estimator.py' niet vinden. Error: {e}")
    def estimate_from_records(*args, **kwargs): return None

try: import resp_rr_param_sets 
except ImportError: resp_rr_param_sets = None

try: from .feedback_engine import engine as fb_engine
except ImportError:
    try: from server.feedback_engine import engine as fb_engine
    except: fb_engine = None

log = logging.getLogger("sensor-ingest")

# ------------ directories ------------
LOG_DIR = (ROOT_DIR / "logs").resolve()
WEB_DIR = (ROOT_DIR / "server/web").resolve()
LOG_FILE_OVERRIDE: Optional[Path] = None
LOG_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)
SERVER_START_TS = datetime.now().strftime('%Y%m%d_%H%M%S')

# ------------ LOGGING ------------
BULK_MINIMAL_LOG = False  
BULK_SIGNAL_WHITELIST = {"resp_rr", "guidance", "hr_derived", "BreathTarget"} 

# ------------ EDR init ------------
FS_ECG = float(os.getenv("ECG_FS", "130.0"))

try:
    import orjson
    def dumps(obj: Any) -> str: return orjson.dumps(obj, option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_NON_STR_KEYS).decode()
except Exception:
    def dumps(obj: Any) -> str: return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"

# --- HELPER FUNCTIES ---

def enrich_with_dt(obj: dict) -> dict:
    """
    Voegt 'dt' toe als EERSTE sleutel met format DD-MM-YYYY HH:MM:SS:MMM
    """
    now = datetime.now()
    # Milliseconden (3 cijfers)
    ms = int(now.microsecond / 1000)
    dt_str = now.strftime("%d-%m-%Y %H:%M:%S") + f":{ms:03d}"
    
    # Nieuw dict maken met dt vooraan
    return {"dt": dt_str, **obj}

def _today_file(device_id: str = None) -> Path:
    global LOG_FILE_OVERRIDE
    if LOG_FILE_OVERRIDE is not None: return LOG_FILE_OVERRIDE
    filename = f"ingest_{SERVER_START_TS}.jsonl"
    if device_id and device_id != "UNKNOWN":
        target_dir = LOG_DIR / device_id
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / filename
    return LOG_DIR / filename

def _get_param_header_line() -> str:
    version = "v1_default"
    if resp_rr_param_sets:
        version = os.getenv("RESP_RR_VERSION", "v1_default")
        try:
            params_obj = resp_rr_param_sets.get_params(version)
            final_dict = {"version": version, **asdict(params_obj)}
        except Exception as e:
            final_dict = {"version": version, "error": f"Could not load params: {e}"}
    else:
        final_dict = {"version": version, "error": "Param sets module missing"}
    
    # Header krijgt ook een timestamp, waarom niet
    return dumps(enrich_with_dt({"parameters": final_dict}))

async def _append_lines(lines: List[str], device_id: str = None) -> str:
    path = _today_file(device_id)
    write_header = False
    if not path.exists() or path.stat().st_size == 0: write_header = True
    async with aiofiles.open(path, "a", encoding="utf-8") as f:
        if write_header: await f.write(_get_param_header_line())
        await f.writelines(lines)
    return str(path.resolve())

def _to_epoch_ms(x: Union[int, float, None]) -> Optional[int]:
    if x is None: return None
    try: t = int(x)
    except Exception: return None
    if t > 10_000_000_000_000: return t // 1_000_000
    if 1_000_000_000 < t < 10_000_000_000: return t * 1000
    if 1_000_000_000_000 < t < 10_000_000_000_000: return t // 1000
    if 1_000_000_000_000 <= t <= 10_000_000_000_000: return t
    return None

def _build_breath_instruction(cycle: dict) -> str:
    if not cycle: return ""
    try:
        parts = []
        p_in = cycle.get("in", 0); p_h1 = cycle.get("hold1", 0)
        p_out = cycle.get("out", 0); p_h2 = cycle.get("hold2", 0)
        parts.append(f"Adem {p_in} seconden in")
        if p_h1 > 0: parts.append(f"hou {p_h1} seconden vast")
        parts.append(f"adem {p_out} seconden uit")
        if p_h2 > 0: parts.append(f"hou {p_h2} seconden vast")
        return ", ".join(parts) + "."
    except Exception: return ""

def _derive_resp_lines(obj: dict, session: Any) -> List[str]:
    out: List[str] = []
    signal_type = obj.get("signal")

    if signal_type == "BreathTarget":
        val = obj.get("TargetRR", 0)
        tech_name = obj.get("technique")
        
        session.current_target_rr = val if val is not None else 0.0
        session.current_breath_cycle = obj.get("breath_cycle")
        
        if val > 0:
            if tech_name and hasattr(session, "activate_technique"):
                session.activate_technique(tech_name)
        else:
            if hasattr(session, "reset_params"):
                session.reset_params()
        
        active_ver = getattr(session, "active_version_name", "Unknown")
        obj["active_param_version"] = active_ver
        
        # Voeg DT toe
        out.append(dumps(enrich_with_dt(obj))) 
        return out

    if signal_type != "ecg": return []

    session.ecg_buffer.append(obj)
    START_THRESHOLD = 20 
    if len(session.ecg_buffer) < START_THRESHOLD: 
        return []

    try:
        current_params = getattr(session, "active_params", {})
        res = estimate_from_records(list(session.ecg_buffer), fs_hint=FS_ECG, params=current_params)
    except Exception: return []

    if not res: return []

    est_rr = res.get("est_rr"); tijd = res.get("tijd"); ts_per_beat = res.get("ts_per_beat")
    inhale = res.get("inhale"); exhale = res.get("exhale"); rr_ms = res.get("rr_ms")
    last_ts = session.last_emitted_ts if session.last_emitted_ts is not None else -1

    if est_rr is not None and ts_per_beat is not None:
        for i in range(len(est_rr)):
            v = est_rr[i]; ts_val = ts_per_beat[i] if i < len(ts_per_beat) else np.nan
            if v is None or (isinstance(v, float) and (not np.isfinite(v))): continue
            if not (isinstance(ts_val, (int, float)) and np.isfinite(ts_val)): continue
            if ts_val <= last_ts: continue
            
            ts_ms_int = int(ts_val)
            line_data = {
                "signal": "resp_rr", "ts": ts_ms_int,
                "tijd": tijd[i] if tijd is not None and i < len(tijd) else "",
                "estRR": float(est_rr[i]),
                "inhale": inhale[i] if inhale is not None and i < len(inhale) else "",
                "exhale": exhale[i] if exhale is not None and i < len(exhale) else "",
            }
            # Voeg DT toe
            out.append(dumps(enrich_with_dt(line_data)))
            
            if fb_engine:
                text, audio_text, color = fb_engine.get_feedback(session.current_target_rr, float(est_rr[i]))
                if text:
                    # Als we in de "Start" (Blauw/accent) fase zitten:
                    if color == "accent" and session.current_breath_cycle:
                        
                        instruction = _build_breath_instruction(session.current_breath_cycle)
                        
                        tech_name_raw = getattr(session, "current_technique", None)
                        if tech_name_raw:
                            if "(" in tech_name_raw:
                                tech_name_clean = tech_name_raw.split("(")[0].strip()
                            else:
                                tech_name_clean = tech_name_raw.strip()
                            
                            if instruction:
                                instruction = f"{tech_name_clean}... {instruction}"
                        
                        if instruction and audio_text:
                            audio_text = f"{audio_text}... {instruction}"

                    guidance_rec = {
                        "signal": "guidance", "ts": ts_ms_int,
                        "text": text, "audio_text": audio_text, "color": color,
                        "target": session.current_target_rr, "actual": float(est_rr[i])
                    }
                    # Voeg DT toe
                    out.append(dumps(enrich_with_dt(guidance_rec)))
            last_ts = max(last_ts, ts_ms_int)

    if rr_ms is not None and ts_per_beat is not None and len(rr_ms) > 0:
        for k in range(len(rr_ms)-1, -1, -1):
            rr = rr_ms[k]
            if rr is None or (isinstance(rr, float) and (not np.isfinite(rr))) or rr <= 0: continue
            idx = min(k+1, len(ts_per_beat)-1)
            ts_hr = ts_per_beat[idx] if idx < len(ts_per_beat) and np.isfinite(ts_per_beat[idx]) else None
            bpm = 60000.0 / float(rr)
            rec = {"signal": "hr_derived", "ts": int(ts_hr) if ts_hr is not None else int(datetime.now().timestamp()*1000), "bpm": float(bpm)}
            # Voeg DT toe
            out.append(dumps(enrich_with_dt(rec)))
            break

    if ts_per_beat is not None and est_rr is not None and len(est_rr) > 0:
        idx_last = None
        for i in range(len(est_rr)-1, -1, -1):
            if (np.isfinite(est_rr[i]) and i < len(ts_per_beat) and np.isfinite(ts_per_beat[i])):
                if ts_per_beat[i] > last_ts: idx_last = i; break
        if idx_last is not None:
            ts_ms = int(ts_per_beat[idx_last]); br = float(est_rr[idx_last])
            rec = {"signal": "resp", "ts": ts_ms, "fs": 0.0, "t": [], "v": [], "br_bpm": br, "br_bpm_psd": br, "br_bpm_td": br}
            # Voeg DT toe
            out.append(dumps(enrich_with_dt(rec)))

    session.last_emitted_ts = last_ts if last_ts >= 0 else session.last_emitted_ts
    return out

def reset_runtime_state() -> None: pass
def rotate_logfile(new_name: Optional[str] = None) -> str:
    global LOG_FILE_OVERRIDE
    if new_name: path = LOG_DIR / new_name
    else: path = LOG_DIR / f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    LOG_FILE_OVERRIDE = path
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "a", encoding="utf-8") as _f: pass
    except Exception: pass
    return str(path.resolve())