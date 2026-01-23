# server/edr_extractor.py
# -*- coding: utf-8 -*-
from typing import Iterable, Dict, Any, List, Optional
import numpy as np

# AANGEPAST: Direct importeren uit de hoofdmap (sys.path)
# Dus NIET 'from .resp_rr_estimator' en NIET 'from server.resp_rr_estimator'
from resp_rr_estimator import estimate_from_arrays

def estimate_from_records(records: Iterable[Dict[str, Any]], fs_hint: Optional[float] = None) -> Dict[str, Any]:
    all_samples: List[int] = []
    ts_list: List[int] = []
    block_sizes: List[int] = []
    per_sample_t: List[float] = []
    
    for rec in records:
        if rec.get("signal") != "ecg":
            continue
        if "samples" in rec and isinstance(rec["samples"], list):
            all_samples.extend(int(v) for v in rec["samples"])
            block_sizes.append(len(rec["samples"]))
            if "ts" in rec:
                ts_list.append(int(rec["ts"]))
        elif "ecg" in rec:
            all_samples.append(int(rec["ecg"]))
            t = rec.get("timestamp")
            if t is not None:
                try:
                    per_sample_t.append(float(t))
                except Exception:
                    pass
                    
    if not all_samples:
        raise ValueError("Geen ECG-samples in records.")
        
    sig_i16 = np.array(all_samples, dtype=np.int16)
    ts_arr = np.array(ts_list, dtype=np.int64) if ts_list else None
    per_sample_arr = np.array(per_sample_t, dtype=float) if per_sample_t else None
    
    return estimate_from_arrays(sig_i16, ts_arr, None, block_sizes if block_sizes else None, per_sample_arr, fs_hint=fs_hint)