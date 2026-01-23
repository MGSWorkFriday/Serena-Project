#!/usr/bin/env python3
# jsonl_rr_estimator_130Hz.py - CLI that delegates to resp_rr_estimator
import sys, os, numpy as np
from resp_rr_estimator import estimate_from_jsonl

def estimate_rr_from_jsonl(jsonl_path, out_csv="resprate.csv", fs_hint=None, plot=False):
    res = estimate_from_jsonl(jsonl_path, fs_hint=fs_hint)
    sm = res["est_rr"]
    idx = np.arange(len(sm), dtype=float)
    arr = np.column_stack([idx, res["ts_per_beat"], res["tijd"], sm, res["inhale"], res["exhale"]])
    np.savetxt(out_csv, arr, delimiter=", ", fmt=['%f','%0.0f','%s','%f','%s','%s'],
               header="sample, ts, tijd, estRR, inhale, exhale", comments="")
    return res["fs"], res["rpeaks"], sm


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Gebruik: python jsonl_rr_estimator_130Hz.py <input.jsonl of map>")
        raise SystemExit(1)

    path = sys.argv[1]

    if os.path.isdir(path):
        # Als het een map is → verwerk alle .jsonl-bestanden
        jsonl_files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".jsonl")]
        if not jsonl_files:
            print(f"❌ Geen .jsonl-bestanden gevonden in {path}")
            raise SystemExit(1)

        for jsonl in jsonl_files:
            out_csv = jsonl + ".csv"
            print(f"➡️  Verwerk {os.path.basename(jsonl)} ...", end=" ")
            try:
                fs_used, rpeaks, rr_sm = estimate_rr_from_jsonl(jsonl, out_csv=out_csv)
                print(f"✅ Klaar (fs={fs_used:.3f} Hz, R-peaks={len(rpeaks)})")
            except Exception as e:
                print(f"❌ Fout bij {jsonl}: {e}")

    elif os.path.isfile(path):
        # Enkel bestand
        out_csv = path + ".csv"
        fs_used, rpeaks, rr_sm = estimate_rr_from_jsonl(path, out_csv=out_csv)
        print(f"✅ Klaar. fs gebruikt: {fs_used:.3f} Hz, R-peaks: {len(rpeaks)}, CSV: {out_csv}")

    else:
        print(f"❌ Pad niet gevonden: {path}")
        raise SystemExit(1)
