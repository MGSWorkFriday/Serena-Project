# algorithms.py
from collections import deque
from statistics import median

class RobustECGHRDetector:
    """
    Live HR/RR (~130 Hz) met T-wave suppressie:
    - baseline removal
    - smoothing
    - adaptieve drempel (MAD)
    - dynamische refractory window
    """
    def __init__(self, sr_hz=130, base_win_s=0.6, smooth_win_s=0.12, k=3.0):
        self.sr = sr_hz
        self.dt_ms = 1000.0/sr_hz
        self.base_N = max(3, int(base_win_s*sr_hz))
        self.smooth_N = max(3, int(smooth_win_s*sr_hz))
        self.k = float(k)

        self.raw = []                 
        self.t0_ms = None             
        self.last_peak_idx = -10_000  
        self.peak_times_ms = []       

        # refractory grenzen
        self._startup_refrac_ms = 350
        self._min_refrac_ms = 300
        self._max_refrac_ms = 600

        self.polarity = 1             
        self.base_q = deque(); self.base_sum = 0.0
        self.smooth_q = deque(); self.smooth_sum = 0.0

    def _mad(self, arr):
        if not arr: return 0.0
        m = median(arr)
        return median([abs(x-m) for x in arr])

    def _choose_polarity(self, seg):
        if not seg: return 1
        pos = sorted([x for x in seg if x>0])
        neg = sorted([-x for x in seg if x<0])
        pos_p = pos[int(0.9*len(pos))] if pos else 0.0
        neg_p = neg[int(0.9*len(neg))] if neg else 0.0
        return 1 if pos_p>=neg_p else -1

    def _dyn_refrac_ms(self):
        rrs = self.rr_list_ms(8)
        if len(rrs) >= 3:
            mr = median(rrs)
            return int(max(self._min_refrac_ms, min(self._max_refrac_ms, 0.45*mr)))
        return self._startup_refrac_ms

    def add_batch(self, last_ts_ms: int, values):
        if not values: return
        start_ts_ms = int(last_ts_ms - (len(values)-1)*self.dt_ms)
        if self.t0_ms is None:
            self.t0_ms = start_ts_ms

        start_idx = len(self.raw)
        self.raw.extend(values)

        if start_idx < int(2*self.sr) and len(self.raw)>=int(2*self.sr):
            seg = self.raw[:int(2*self.sr)]
            mu = sum(seg)/len(seg)
            seg = [x-mu for x in seg]
            self.polarity = self._choose_polarity(seg)

        self._detect_range(start_idx, len(self.raw)-1)

    def _detect_range(self, i0, i1):
        if i0<0: i0=0
        if i1-i0<3: return

        for i in range(i0, i1+1):
            x = float(self.raw[i])

            self.base_q.append(x); self.base_sum += x
            if len(self.base_q)>self.base_N:
                self.base_sum -= self.base_q.popleft()
            base = self.base_sum/len(self.base_q)

            detr = (x - base) * self.polarity

            self.smooth_q.append(detr); self.smooth_sum += detr
            if len(self.smooth_q)>self.smooth_N:
                self.smooth_sum -= self.smooth_q.popleft()
            smooth = self.smooth_sum/len(self.smooth_q)

            if i < self.base_N + self.smooth_N:
                continue

            hist_N = int(1.5*self.sr)
            j0 = max(0, i-hist_N)
            hist = self.raw[j0:i+1]
            mu = sum(hist)/len(hist)
            detr_hist = [(v-mu)*self.polarity for v in hist]
            mad = self._mad(detr_hist)
            thr = (median(detr_hist) if detr_hist else 0.0) + self.k*(mad if mad>0 else 1.0)

            if smooth < thr:
                continue

            if i<=0 or i>=len(self.raw)-1: 
                continue
            left = (self.raw[i-1]-mu)*self.polarity
            center = (self.raw[i]-mu)*self.polarity
            right = (self.raw[i+1]-mu)*self.polarity
            if not (left<=center>=right):
                continue

            dyn_ms = self._dyn_refrac_ms()
            dyn_samp = int(dyn_ms / self.dt_ms)
            if i - self.last_peak_idx < dyn_samp:
                continue

            t_ms = (self.t0_ms or 0) + int(i*self.dt_ms)
            self.peak_times_ms.append(t_ms)
            self.last_peak_idx = i
            if len(self.peak_times_ms)>20:
                self.peak_times_ms = self.peak_times_ms[-20:]

    def rr_list_ms(self, last_n=None):
        pts = self.peak_times_ms
        if len(pts)<2: return []
        rrs = [pts[i]-pts[i-1] for i in range(1,len(pts))]
        return rrs[-(last_n or 8):]

    def bpm(self):
        rrs = self.rr_list_ms()
        if not rrs: return None
        min_rr = self._dyn_refrac_ms()
        rrs_f = [r for r in rrs if r >= min_rr]
        if not rrs_f: return None
        m = median(rrs_f)
        if m<=0: return None
        bpm = 60000.0/m
        return int(max(40, min(200, round(bpm))))