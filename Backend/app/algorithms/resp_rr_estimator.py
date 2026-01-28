# -*- coding: utf-8 -*-
"""
resp_rr_estimator.py — ECG to Respiratory Rate Estimation
Migrated from SerenaWebApp/pythonbleakgui_server/resp_rr_estimator.py
"""
from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from scipy import signal
from scipy.signal import find_peaks


# ---------------- Helper functies ----------------

def _hann(n: int) -> np.ndarray:
    return 0.5 - 0.5*np.cos(2*np.pi*np.arange(n)/max(1,n-1))


def _parabolic_interp(y: np.ndarray, i: int) -> Tuple[float, float]:
    if i <= 0 or i >= len(y)-1:
        return float(i), float(y[i])
    y0, y1, y2 = y[i-1], y[i], y[i+1]
    denom = (2*(2*y1 - y0 - y2))
    if denom == 0:
        return float(i), float(y1)
    delta = (y0 - y2) / denom
    x_ref = i + delta
    y_ref = y1 - 0.25*(y0 - y2)*delta
    return float(x_ref), float(y_ref)


def _butter_bandpass_filtfilt(x: np.ndarray, fs: float, low_hz: float, high_hz: float, order: int = 2) -> np.ndarray:
    nyq = fs / 2.0
    b, a = signal.butter(order, [low_hz/nyq, high_hz/nyq], btype="band")
    return signal.filtfilt(b, a, x)


def _moving_window_abs_mean(x: np.ndarray, win: int) -> np.ndarray:
    y = np.zeros_like(x, dtype=float)
    acc = 0.0
    ax = np.abs(x)
    for i, v in enumerate(ax):
        acc += v
        if i >= win:
            acc -= ax[i - win]
            y[i] = acc / win
        else:
            y[i] = acc / (i + 1)
    return y


def _detect_r_peaks(ecg_raw: np.ndarray, fs: float, cfg: Dict) -> np.ndarray:
    """Detecteert R-toppen met behulp van de meegegeven configuratie (cfg)."""
    x = _butter_bandpass_filtfilt(ecg_raw, fs, cfg["BP_LOW_HZ"], cfg["BP_HIGH_HZ"], order=2)
    w1 = max(1, int(round(cfg["MWA_QRS_SEC"]  * fs)))
    w2 = max(1, int(round(cfg["MWA_BEAT_SEC"] * fs)))
    mwa_qrs  = _moving_window_abs_mean(x, w1)
    mwa_beat = _moving_window_abs_mean(x, w2)
    block = (mwa_qrs > mwa_beat).astype(int)
    min_seg = int(round(cfg["MIN_SEG_SEC"] * fs))
    refr    = int(round(cfg["MIN_RR_SEC"]  * fs))
    peaks: List[int] = []
    on: Optional[int] = None
    for i in range(1, len(block)):
        if on is None and block[i-1]==0 and block[i]==1:
            on = i
        elif on is not None and block[i-1]==1 and block[i]==0:
            off = i-1
            if (off - on) > min_seg:
                seg = x[on:off+1]
                pk = on + int(np.argmax(seg))
                if not peaks or (pk - peaks[-1] > refr):
                    peaks.append(pk)
            on = None
    return np.array(peaks, dtype=int)


def _refine_r_peaks(sig: np.ndarray, rpeaks: np.ndarray) -> np.ndarray:
    if rpeaks.size == 0:
        return rpeaks
    out: List[int] = []
    for idx in rpeaks:
        i = int(idx)
        if i <= 0 or i >= len(sig)-1:
            out.append(i); continue
        while i > 0 and sig[i] < sig[i-1]:
            i -= 1
        while i < len(sig)-1 and sig[i] < sig[i+1]:
            i += 1
        out.append(i)
    return np.array(out, dtype=int)


def _extract_qrs_stacks(ecg_raw: np.ndarray, rpeaks: np.ndarray, fs: float, cfg: Dict) -> np.ndarray:
    half = int(round(cfg["QRS_HALF_SEC"] * fs))
    x = _butter_bandpass_filtfilt(ecg_raw, fs, cfg["BP_LOW_HZ"], cfg["BP_HIGH_HZ"], order=2)
    beats = np.zeros((2*half+1, rpeaks.size))
    N = len(x)
    for k, rp in enumerate(rpeaks):
        seg = np.clip(np.arange(rp - half, rp + half + 1), 0, N-1)
        beats[:, k] = x[seg]
    return beats


def _estimate_bpm_from_section(section: np.ndarray, rr_med_ms: float, cfg: Dict) -> float:
    if not (np.isfinite(rr_med_ms) and section.size >= 4):
        return np.nan
    s = section - np.mean(section)
    sw = s * _hann(len(s))
    nfft = int(cfg["FFT_LENGTH"])
    if nfft < len(sw):
        nfft = 1 << (len(sw)-1).bit_length()
    sp = np.fft.rfft(sw, n=nfft)
    ps = (sp * np.conj(sp)).real
    f_cb = np.fft.rfftfreq(nfft, d=1.0)
    beats_per_min = 60000.0 / rr_med_ms
    
    f_range = cfg["FREQ_RANGE_CB"]
    bpm_min = cfg["BPM_MIN"]
    bpm_max = cfg["BPM_MAX"]
    h_ratio = cfg["HARMONIC_RATIO"]

    fmin = max(f_range[0], bpm_min / beats_per_min)
    fmax = min(f_range[1], bpm_max / beats_per_min)
    if fmin >= fmax:
        return np.nan
    mask = (f_cb >= fmin) & (f_cb <= fmax)
    if not np.any(mask):
        return np.nan
    idxs = np.where(mask)[0]
    k0 = idxs[np.argmax(ps[idxs])]
    xk, _ = _parabolic_interp(ps, int(k0))
    xk = max(idxs[0], min(idxs[-1], xk))
    f0_cb = np.interp(xk, np.arange(len(f_cb)), f_cb)
    bpm = f0_cb * beats_per_min
    
    def _ps_at(freq: float) -> float:
        if freq <= f_cb[0] or freq >= f_cb[-1]: return 0.0
        k = int(np.argmin(np.abs(f_cb - freq))); return float(ps[k])
    
    ps_f   = _ps_at(f0_cb)
    ps_2f  = _ps_at(min(0.5, 2.0*f0_cb))
    ps_hf  = _ps_at(max(f_range[0], 0.5*f0_cb))
    
    if ps_2f > h_ratio * max(ps_f, 1e-12):
        bpm2 = 2.0*bpm
        if bpm_min <= bpm2 <= bpm_max: bpm = bpm2
    elif ps_hf > h_ratio * max(ps_f, 1e-12):
        bpm2 = 0.5*bpm
        if bpm_min <= bpm2 <= bpm_max: bpm = bpm2
    return float(bpm)


# ---------------- Publieke API ----------------

def estimate_from_records(records: List[dict], fs_hint: float = 130.0, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Zet list-of-records om naar arrays en roept de estimator aan.
    """
    if not records:
        return None
        
    all_samples = []
    ts_list = []
    block_sizes = []
    
    for r in records:
        samps = r.get("samples", [])
        if not samps: continue
        
        if isinstance(samps, (list, tuple, np.ndarray)):
             all_samples.extend([int(x) for x in samps])
             block_sizes.append(len(samps))
        
        if "ts" in r:
            ts_list.append(int(r["ts"]))

    if not all_samples:
        return None

    sig_i16 = np.array(all_samples, dtype=np.int16)
    ts_arr = np.array(ts_list, dtype=np.int64) if ts_list else None

    try:
        return estimate_from_arrays(sig_i16, ts_arr, fs_est=None, block_sizes=block_sizes, per_sample_t=None, fs_hint=fs_hint, params=params)
    except Exception as e:
        print(f"[ESTIMATOR] Fout tijdens berekening: {e}") 
        return None


def estimate_from_arrays(sig_i16: np.ndarray,
                         ts: Optional[np.ndarray],
                         fs_est: Optional[float],
                         block_sizes: Optional[List[int]],
                         per_sample_t: Optional[np.ndarray],
                         fs_hint: Optional[float] = None,
                         params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Core estimation function.
    Accepts params dict directly (from MongoDB ParameterSet).
    """
    # Build config from params
    if params is None:
        params = {}
    
    # Default values
    cfg = {
        "BP_LOW_HZ": params.get("BP_LOW_HZ", 4.0),
        "BP_HIGH_HZ": params.get("BP_HIGH_HZ", 20.0),
        "MWA_QRS_SEC": params.get("MWA_QRS_SEC", 0.12),
        "MWA_BEAT_SEC": params.get("MWA_BEAT_SEC", 0.6),
        "MIN_SEG_SEC": params.get("MIN_SEG_SEC", 0.08),
        "MIN_RR_SEC": params.get("MIN_RR_SEC", 0.3),
        "QRS_HALF_SEC": params.get("QRS_HALF_SEC", 0.04),
        "HEARTBEAT_WINDOW": params.get("HEARTBEAT_WINDOW", 32),
        "FFT_LENGTH": params.get("FFT_LENGTH", 512),
        "FREQ_RANGE_CB": params.get("FREQ_RANGE_CB", [0.03, 0.5]),
        "SMOOTH_WIN": params.get("SMOOTH_WIN", 32),
        "BPM_MIN": params.get("BPM_MIN", 4.0),
        "BPM_MAX": params.get("BPM_MAX", 40.0),
        "HARMONIC_RATIO": params.get("HARMONIC_RATIO", 1.4),
    }
    
    fs = float(fs_hint) if fs_hint else (float(fs_est) if fs_est else 130.0)
    sig = sig_i16.astype(float)
    sig -= np.median(sig)

    # R-Peak detectie
    r0 = _detect_r_peaks(sig, fs, cfg)
    r  = _refine_r_peaks(sig, r0)
    if r.size < 4:
        raise RuntimeError(f"Te weinig R-peaks ({r.size}) gevonden; check signaalkwaliteit.")

    # EDR (RMS) berekening
    qrs = _extract_qrs_stacks(sig, r, fs, cfg)
    rms = np.sqrt(np.mean(qrs**2, axis=0))
    rr_ms = 1000.0 * np.diff(r) / fs

    # BPM Schatting (Spectraal)
    est: List[float] = []
    h_win = int(cfg["HEARTBEAT_WINDOW"])
    s_win = int(cfg["SMOOTH_WIN"])

    for i in range(rms.size):
        if i < h_win:
            section = rms[0:i]
            rr_med_ms = np.median(rr_ms[0:i]) if i > 0 and rr_ms.size>0 else np.nan
        else:
            section = rms[i-h_win:i]
            start  = max(0, i-h_win-1)
            stop   = max(0, i-1)
            rr_slice = rr_ms[start:stop] if stop > start else rr_ms[0:i]
            rr_med_ms = np.median(rr_slice) if rr_slice.size>0 else np.nan

        bpm = _estimate_bpm_from_section(section, rr_med_ms, cfg)
        est.append(bpm)
    est = np.asarray(est, dtype=float)

    # Smoothing van BPM
    sm = np.copy(est)
    for i in range(len(est)):
        if i >= s_win:
            sm[i] = np.nanmedian(est[i-s_win:i])

    # Tijd Mapping
    sample_ts_ms = None
    if per_sample_t is not None and isinstance(per_sample_t, np.ndarray) and per_sample_t.size == sig_i16.size:
        sample_ts_ms = per_sample_t*1000.0
    elif ts is not None and block_sizes:
        sample_ts_ms = np.empty(sig_i16.size, dtype=float)
        cursor = 0
        for b, bsize in enumerate(block_sizes):
            if b >= len(ts): break
            t0 = float(ts[b])
            if bsize <= 0: continue
            offs = (np.arange(bsize, dtype=float)/fs)*1000.0
            end = cursor + bsize
            take = max(0, end - cursor)
            sample_ts_ms[cursor:end] = t0 + offs[:take]
            cursor = end

    ts_per_beat = np.full(len(sm), np.nan, dtype=float)
    tijd = np.array([''] * len(sm), dtype=object)
    
    if sample_ts_ms is not None and r.size == len(sm):
        for i in range(len(sm)):
            rp = int(r[i])
            if 0 <= rp < len(sample_ts_ms) and np.isfinite(sm[i]):
                ts_per_beat[i] = sample_ts_ms[rp]
        
        valid_idx = np.where(np.isfinite(ts_per_beat))[0]
        if valid_idx.size:
            base_ts = ts_per_beat[valid_idx[0]]
            for i in valid_idx:
                rel_ms = ts_per_beat[i] - base_ts
                total_ms = int(round(rel_ms))
                h, rem = divmod(total_ms, 3600_000)
                m, rem = divmod(rem, 60_000)
                s, ms = divmod(rem, 1000)
                tijd[i] = f"{h:02d}:{m:02d}:{s:02d}.{ms:03d} UTC"

    # INHALE/EXHALE DETECTIE
    inhale = np.array([''] * len(sm), dtype=object)
    exhale = np.array([''] * len(sm), dtype=object)

    if rms.size >= 10:
        est_resp_bpm = np.nanmedian(sm[-20:]) if sm.size >= 20 else np.nanmedian(sm)
        if np.isnan(est_resp_bpm) or est_resp_bpm <= 3: 
            est_resp_bpm = 10.0
        
        avg_rr_sec = (np.nanmedian(rr_ms) / 1000.0) if (rr_ms is not None and rr_ms.size > 0) else 0.8
        if avg_rr_sec <= 0.3: avg_rr_sec = 0.8

        resp_cycle_sec = 60.0 / est_resp_bpm
        target_smooth_sec = min(2.0, max(0.6, resp_cycle_sec * 0.25)) 
        
        smooth_beats = int(target_smooth_sec / avg_rr_sec)
        smooth_beats = max(3, smooth_beats)
        if smooth_beats % 2 == 0: smooth_beats += 1

        window = np.hanning(smooth_beats)
        window = window / window.sum()
        rms_smooth = np.convolve(rms, window, mode='same')

        trend_win = max(30, int((resp_cycle_sec * 2) / avg_rr_sec))
        trend = _moving_window_abs_mean(rms_smooth, trend_win)
        rms_detrended = rms_smooth - trend

        min_dist_beats = max(1, int((resp_cycle_sec * 0.4) / avg_rr_sec))
        local_ptp = np.percentile(rms_detrended, 95) - np.percentile(rms_detrended, 5)
        prom_val = max(0.001, local_ptp * 0.15)

        peaks_e, _ = find_peaks(rms_detrended, distance=min_dist_beats, prominence=prom_val)
        peaks_i, _ = find_peaks(-rms_detrended, distance=min_dist_beats, prominence=prom_val)

        for p in peaks_e:
            if p < len(exhale): exhale[p] = 'E'
        
        for p in peaks_i:
            if p < len(inhale): inhale[p] = 'I'

    return {
        "fs": fs,
        "rpeaks": r,
        "est_rr": sm,
        "ts_per_beat": ts_per_beat,
        "tijd": tijd,
        "inhale": inhale,
        "exhale": exhale,
        "rr_ms": rr_ms,
        "edr": None, "t_edr": None, "rr_times": None, "rr_bpm": None,
    }
