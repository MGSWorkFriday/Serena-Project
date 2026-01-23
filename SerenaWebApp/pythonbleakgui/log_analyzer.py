# -*- coding: utf-8 -*-
import argparse
import json
import glob
import os
import statistics
from datetime import datetime

def parse_target_from_filename(filename):
    """
    Haalt de ademhalingstimings uit de bestandsnaam.
    Verwacht formaat: ...-<in>_<hold1>_<out>_<hold2>_...
    """
    try:
        basename = os.path.basename(filename)
        if "-" not in basename:
            return None
        
        part_after_dash = basename.split("-", 1)[1]
        parts = part_after_dash.split("_")
        
        if len(parts) < 4:
            return None
            
        t_in = float(parts[0])
        t_hold1 = float(parts[1])
        t_out = float(parts[2])
        t_hold2 = float(parts[3])
        
        total_cycle_sec = t_in + t_hold1 + t_out + t_hold2
        
        if total_cycle_sec <= 0:
            return 0
            
        target_bpm = 60.0 / total_cycle_sec
        return target_bpm
        
    except Exception:
        return None

def analyze_file(filepath):
    est_rr_values = []
    version = "Onbekend"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                try:
                    data = json.loads(line)
                    if "parameters" in data:
                        params = data["parameters"]
                        if "version" in params:
                            version = params["version"]
                        elif "version" in data:
                            version = data["version"]
                            
                    if data.get("signal") == "resp_rr":
                        val = data.get("estRR")
                        if val is not None and isinstance(val, (int, float)):
                            est_rr_values.append(float(val))
                            
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        return f"Fout: {e}", None

    return version, est_rr_values

def main():
    parser = argparse.ArgumentParser(description="Analyseer sensor logfiles.")
    parser.add_argument("--folder", type=str, required=True, help="Pad naar de map met logfiles")
    args = parser.parse_args()

    if not os.path.exists(args.folder):
        print(f"[FOUT] Map bestaat niet: {args.folder}")
        return

    # Zoek alle .jsonl bestanden
    pattern = os.path.join(args.folder, "*.jsonl")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"[INFO] Geen .jsonl bestanden gevonden in {args.folder}")
        return

    # Bepaal bestandsnaam
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"analyse_report_{timestamp}.txt"
    report_path = os.path.join(args.folder, report_filename)

    print(f"[INFO] Rapport wordt geschreven naar: {report_path}")

    # Schrijven naar bestand
    try:
        with open(report_path, "w", encoding="utf-8") as f_out:
            
            def output(msg):
                print(msg)
                f_out.write(msg + "\n")

            header = f"{'BESTAND':<40} | {'VERSIE':<13} | {'TARGET':<6} | {'GEM':<6} | {'LAATSTE 20':<10} | {'DELTA':<6}"
            sep = "-" * 100
            
            output(header)
            output(sep)

            for file_path in files:
                filename = os.path.basename(file_path)
                target = parse_target_from_filename(filename)
                target_str = f"{target:.1f}" if target else "??"
                
                version, values = analyze_file(file_path)
                
                if not values:
                    output(f"{filename[:38]:<40} | {version[:13]:<13} | {target_str:<6} | {'GEEN DATA':<20}")
                    continue
                    
                mean_val = statistics.mean(values)
                
                n_last = 20
                last_segment = values[-n_last:] if len(values) > n_last else values
                last_mean = statistics.mean(last_segment)
                
                delta_str = ""
                if target:
                    diff = last_mean - target
                    delta_str = f"{diff:+.2f}"
                    if abs(diff) < 1.0:
                        delta_str += " (OK)"
                    elif abs(diff) > 5.0:
                        delta_str += " (!)"

                output(f"{filename[:38]:<40} | {version[:13]:<13} | {target_str:<6} | {mean_val:.1f}   | {last_mean:.1f}       | {delta_str}")

            output(sep)
            output(f"[KLAAR] {len(files)} bestanden geanalyseerd.")
    
    except Exception as e:
        print(f"[FOUT] Kon rapportbestand niet schrijven: {e}")
        return

    # --- HIER OPENEN WE HET BESTAND ---
    # We doen dit buiten de 'with open' zodat het bestand zeker gesloten/opgeslagen is.
    try:
        print(f"[INFO] Rapport openen...")
        os.startfile(report_path)
    except Exception as e:
        print(f"[WARN] Kon bestand niet automatisch openen: {e}")

if __name__ == "__main__":
    main()