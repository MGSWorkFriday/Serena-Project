# -*- coding: utf-8 -*-
"""Signal processing service"""
from __future__ import annotations

import logging
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.database import get_database
from app.algorithms.resp_rr_estimator import estimate_from_records
from app.services.stream_manager import stream_manager
from app.services.feedback_generator import feedback_generator
from app.schemas.signal import SignalRecord

logger = logging.getLogger(__name__)

# ECG sampling frequency (Hz)
FS_ECG = 130.0
START_THRESHOLD = 20  # Minimum buffer size before processing


class SignalProcessor:
    """Processes signals and generates derived data"""
    
    def __init__(self):
        # ECG buffers per session: session_id -> list of ECG records
        self._ecg_buffers: Dict[str, List[dict]] = {}
    
    async def process_ecg_signal(
        self,
        ecg_record: Dict[str, Any],
        session_id: str,
        db
    ):
        """Process ECG signal and generate RR estimation"""
        try:
            # Get or create buffer for session
            if session_id not in self._ecg_buffers:
                self._ecg_buffers[session_id] = []
            
            buffer = self._ecg_buffers[session_id]
            buffer.append(ecg_record)
            
            # Get session to determine buffer size and parameters
            session_doc = await db.sessions.find_one({"session_id": session_id})
            if not session_doc:
                logger.warning(f"Session {session_id} not found")
                return
            
            # Get parameter set for this session
            param_version = session_doc.get("param_version", "v1_default")
            param_doc = await db.parameter_sets.find_one({"version": param_version})
            
            if not param_doc:
                logger.warning(f"Parameter set {param_version} not found, using defaults")
                params = {}
            else:
                from app.schemas.parameter_set import ParameterSet
                param_set = ParameterSet.from_dict(param_doc)
                params = param_set.to_params_dict()
            
            buffer_size = params.get("BUFFER_SIZE", 200)
            
            # Keep buffer size limited
            if len(buffer) > buffer_size:
                buffer = buffer[-buffer_size:]
                self._ecg_buffers[session_id] = buffer
            
            # Minimum buffer size before processing
            if len(buffer) < START_THRESHOLD:
                return
            
            # Process ECG buffer
            try:
                result = estimate_from_records(
                    list(buffer),
                    fs_hint=FS_ECG,
                    params=params
                )
            except Exception as e:
                logger.error(f"Error in RR estimation: {e}", exc_info=True)
                return
            
            if not result:
                return
            
            # Get session info for target RR
            target_rr = session_doc.get("target_rr", 0.0)
            technique_name = session_doc.get("technique_name")
            # Get breath_cycle from most recent BreathTarget signal
            breath_cycle = None
            if target_rr > 0:
                breath_target = await db.signals.find_one(
                    {"session_id": session_id, "signal": "BreathTarget"},
                    sort=[("ts", -1)]
                )
                if breath_target:
                    breath_cycle = breath_target.get("breath_cycle")
            
            est_rr = result.get("est_rr")
            tijd = result.get("tijd")
            ts_per_beat = result.get("ts_per_beat")
            inhale = result.get("inhale")
            exhale = result.get("exhale")
            rr_ms = result.get("rr_ms")
            
            # Get last emitted timestamp from session metadata or use -1
            last_emitted_ts = session_doc.get("last_emitted_ts", -1)
            
            # Generate resp_rr signals
            if est_rr is not None and ts_per_beat is not None:
                derived_signals: List[dict] = []
                
                for i in range(len(est_rr)):
                    v = est_rr[i]
                    ts_val = ts_per_beat[i] if i < len(ts_per_beat) else None
                    
                    if v is None or (isinstance(v, float) and (not np.isfinite(v))):
                        continue
                    if not (isinstance(ts_val, (int, float)) and np.isfinite(ts_val)):
                        continue
                    if ts_val <= last_emitted_ts:
                        continue
                    
                    ts_ms_int = int(ts_val)
                    dt = self._parse_dt_from_ts(ts_ms_int)
                    
                    # Create resp_rr signal
                    resp_rr_signal = SignalRecord(
                        device_id=ecg_record["device_id"],
                        signal="resp_rr",
                        ts=ts_ms_int,
                        dt=dt,
                        session_id=session_id,
                        estRR=float(v),
                        tijd=str(tijd[i]) if tijd is not None and i < len(tijd) else "",
                        inhale=str(inhale[i]) if inhale is not None and i < len(inhale) else "",
                        exhale=str(exhale[i]) if exhale is not None and i < len(exhale) else "",
                    )
                    derived_signals.append(resp_rr_signal.to_dict())
                    
                    # Generate feedback
                    if target_rr > 0:
                        visual_text, audio_text, color = await feedback_generator.get_feedback(
                            session_id, target_rr, float(v)
                        )
                        
                        if visual_text:
                            # Build instruction text if in accent phase
                            instruction = ""
                            if color == "accent" and breath_cycle:
                                instruction = self._build_breath_instruction(breath_cycle, technique_name)
                            
                            guidance_signal = SignalRecord(
                                device_id=ecg_record["device_id"],
                                signal="guidance",
                                ts=ts_ms_int,
                                dt=dt,
                                session_id=session_id,
                                text=visual_text,
                                audio_text=f"{audio_text}... {instruction}".strip() if instruction else audio_text,
                                color=color,
                                target=target_rr,
                                actual=float(v),
                            )
                            derived_signals.append(guidance_signal.to_dict())
                    
                    last_emitted_ts = max(last_emitted_ts, ts_ms_int)
                
                # Generate hr_derived signal (from last valid RR interval)
                if rr_ms is not None and ts_per_beat is not None and len(rr_ms) > 0:
                    for k in range(len(rr_ms)-1, -1, -1):
                        rr = rr_ms[k]
                        if rr is None or (isinstance(rr, float) and (not np.isfinite(rr))) or rr <= 0:
                            continue
                        idx = min(k+1, len(ts_per_beat)-1)
                        ts_hr = ts_per_beat[idx] if idx < len(ts_per_beat) and np.isfinite(ts_per_beat[idx]) else None
                        if ts_hr is None:
                            continue
                        
                        bpm = 60000.0 / float(rr)
                        hr_signal = SignalRecord(
                            device_id=ecg_record["device_id"],
                            signal="hr_derived",
                            ts=int(ts_hr),
                            dt=self._parse_dt_from_ts(int(ts_hr)),
                            session_id=session_id,
                            bpm=float(bpm),
                        )
                        derived_signals.append(hr_signal.to_dict())
                        break
                
                # Insert derived signals into database
                if derived_signals:
                    await db.signals.insert_many(derived_signals, ordered=False)
                    
                    # Broadcast all derived signals
                    for sig in derived_signals:
                        await stream_manager.broadcast(sig)
                
                # Update session last_emitted_ts
                if last_emitted_ts > 0:
                    await db.sessions.update_one(
                        {"session_id": session_id},
                        {"$set": {"last_emitted_ts": last_emitted_ts}}
                    )
            
        except Exception as e:
            logger.error(f"Error processing ECG signal: {e}", exc_info=True)
    
    def _parse_dt_from_ts(self, ts: int) -> str:
        """Convert timestamp (ms) to dt string format"""
        dt = datetime.fromtimestamp(ts / 1000.0)
        ms = ts % 1000
        return dt.strftime("%d-%m-%Y %H:%M:%S") + f":{ms:03d}"
    
    def _build_breath_instruction(self, breath_cycle: Dict[str, Any], technique_name: Optional[str] = None) -> str:
        """Build breath instruction text"""
        if not breath_cycle:
            return ""
        try:
            parts = []
            p_in = breath_cycle.get("in", 0)
            p_h1 = breath_cycle.get("hold1", 0)
            p_out = breath_cycle.get("out", 0)
            p_h2 = breath_cycle.get("hold2", 0)
            
            parts.append(f"Adem {p_in} seconden in")
            if p_h1 > 0:
                parts.append(f"hou {p_h1} seconden vast")
            parts.append(f"adem {p_out} seconden uit")
            if p_h2 > 0:
                parts.append(f"hou {p_h2} seconden vast")
            
            instruction = ", ".join(parts) + "."
            
            if technique_name:
                tech_clean = technique_name.split("(")[0].strip() if "(" in technique_name else technique_name.strip()
                instruction = f"{tech_clean}... {instruction}"
            
            return instruction
        except Exception:
            return ""
    
    def clear_buffer(self, session_id: str):
        """Clear ECG buffer for a session"""
        if session_id in self._ecg_buffers:
            del self._ecg_buffers[session_id]
        feedback_generator.clear_session_state(session_id)


# Global signal processor instance
signal_processor = SignalProcessor()
