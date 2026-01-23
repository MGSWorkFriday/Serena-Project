import json
import re
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from typing import List, Dict, Optional

# --- 1. Kern Analyse Functie (Overgenomen en aangepast van de eerdere stap) ---

def analyze_file_intervals(file_path: str) -> Optional[Dict]:
    """
    Analyseert de ademhalingsintervallen ('I' en 'E') in een enkel JSONL-bestand.
    Filtert de eerste 30 seconden (starttijd wordt bepaald door de eerste 'ts').
    """
    
    filename = os.path.basename(file_path)
    
    try:
        with open(file_path, 'r') as f:
            file_content = f.readlines()
    except Exception as e:
        return {
            "Bestandsnaam": filename,
            "Status": f"Fout bij lezen: {e}"
        }

    # 1. Haal het ademhalingsschema uit de bestandsnaam
    match = re.search(r'-(\d+)_(\d+)_(\d+)_(\d+)_', filename)
    if not match:
        respiration_scheme = "N/A (Kon schema niet vinden)"
        scheme_parts = None
    else:
        scheme_parts = [int(p) for p in match.groups()]
        respiration_scheme = f"{scheme_parts[0]}s in, {scheme_parts[1]}s hold, {scheme_parts[2]}s uit, {scheme_parts[3]}s hold"
        
    # 2. Filter en parseer de gegevens na de eerste 30 seconden
    parsed_data = []
    first_timestamp = None

    for line in file_content:
        if line.strip():
            try:
                record = json.loads(line)
                if record.get("signal") == "resp_rr":
                    if first_timestamp is None:
                        first_timestamp = record["ts"]
                    
                    # Filter de eerste 30 seconden (30000 milliseconden)
                    if first_timestamp is not None and record["ts"] - first_timestamp > 30000:
                        parsed_data.append(record)
            except json.JSONDecodeError:
                continue # Sla niet-JSON regels over

    if not parsed_data:
        return {
            "Bestandsnaam": filename,
            "Ademhalingsschema": respiration_scheme,
            "Status": "Geen 'resp_rr' data na de eerste 30 seconden."
        }

    # 3. Verzamel de tijdstippen van in- en uitademingen
    inhale_timestamps = []
    exhale_timestamps = []
    
    # Gebruik de timestamp (ts in milliseconden) voor de berekening
    for record in parsed_data:
        timestamp_sec = record["ts"] / 1000.0 # Converteer naar seconden
        if record.get("inhale") == "I":
            inhale_timestamps.append(timestamp_sec)
        if record.get("exhale") == "E":
            exhale_timestamps.append(timestamp_sec)

    # 4. Bereken de intervallen
    
    # Interval tussen opeenvolgende inademingen
    inhale_intervals = [inhale_timestamps[i] - inhale_timestamps[i-1] for i in range(1, len(inhale_timestamps))]
    
    # Interval tussen opeenvolgende uitademingen
    exhale_intervals = [exhale_timestamps[i] - exhale_timestamps[i-1] for i in range(1, len(exhale_timestamps))]
        
    # 5. Samenvatting van de resultaten
    def summarize_intervals(intervals: List[float], label: str) -> Dict:
        if not intervals:
            return {
                "Aantal momenten": len(inhale_timestamps if label == 'I' else exhale_timestamps),
                "Aantal intervallen": 0,
                "Gemiddelde tijd (sec)": "N/A",
                "Min. tijd (sec)": "N/A",
                "Max. tijd (sec)": "N/A",
            }
        
        return {
            "Aantal momenten": len(inhale_timestamps if label == 'I' else exhale_timestamps),
            "Aantal intervallen": len(intervals),
            "Gemiddelde tijd (sec)": round(sum(intervals) / len(intervals), 3),
            "Min. tijd (sec)": round(min(intervals), 3),
            "Max. tijd (sec)": round(max(intervals), 3),
        }

    results = {
        "Bestandsnaam": filename,
        "Ademhalingsschema": respiration_scheme,
        "Inademing (I)": summarize_intervals(inhale_intervals, "I"),
        "Uitademing (E)": summarize_intervals(exhale_intervals, "E"),
        "Ruw I Intervallen (sec)": [round(i, 3) for i in inhale_intervals],
        "Ruw E Intervallen (sec)": [round(i, 3) for i in exhale_intervals],
    }
    
    return results


# --- 2. GUI Implementatie met Tkinter ---

class LogFileAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Log File Ademhalingsanalyse")
        self.default_log_dir = r"D:\Github\nwevrijdag\pythonbleakgui_server\logs" # Ruwe string voor Windows paden
        self.current_log_dir = tk.StringVar(value=self.default_log_dir)
        
        self.create_widgets()

    def create_widgets(self):
        # Frame voor het pad en de knop
        path_frame = tk.Frame(self, padx=10, pady=10)
        path_frame.pack(fill='x')

        # Label voor het pad
        tk.Label(path_frame, text="Log Map Pad:").pack(side='left', padx=(0, 5))

        # Tekstveld met default waarde
        self.dir_entry = tk.Entry(path_frame, textvariable=self.current_log_dir, width=60)
        self.dir_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        # "Kies map" knop
        choose_button = tk.Button(path_frame, text="Kies Map", command=self.choose_directory)
        choose_button.pack(side='left')

        # Analyse knop
        analyze_button = tk.Button(self, text="Start Analyse op Alle Bestanden", command=self.run_analysis)
        analyze_button.pack(fill='x', padx=10, pady=(0, 10))

        # Uitvoer veld
        tk.Label(self, text="Analyseresultaten (JSON):").pack(fill='x', padx=10, pady=(0, 5))
        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=25, padx=5, pady=5)
        self.output_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

    def choose_directory(self):
        """Opent een dialoogvenster om een nieuwe map te selecteren."""
        new_dir = filedialog.askdirectory(initialdir=self.current_log_dir.get())
        if new_dir:
            self.current_log_dir.set(new_dir)

    def run_analysis(self):
        """Voert de analyse uit op alle .jsonl bestanden in de geselecteerde map."""
        log_dir = self.current_log_dir.get()
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Start analyse in map: {log_dir}\n\n")

        if not os.path.isdir(log_dir):
            messagebox.showerror("Fout", f"Map niet gevonden of ongeldig: {log_dir}")
            self.output_text.insert(tk.END, "FOUT: Map bestaat niet of is ontoegankelijk.")
            return

        # Zoek alle .jsonl bestanden
        all_files = [f for f in os.listdir(log_dir) if f.endswith('.jsonl')]
        
        if not all_files:
            self.output_text.insert(tk.END, "Geen .jsonl bestanden gevonden in deze map.")
            return
            
        # Voer de analyse per bestand uit
        all_results = []
        for file_name in all_files:
            file_path = os.path.join(log_dir, file_name)
            result = analyze_file_intervals(file_path)
            if result:
                all_results.append(result)
            
            # Voortgangsweergave
            self.output_text.insert(tk.END, f"Bestand geanalyseerd: {file_name}\n")
            self.output_text.see(tk.END) # Scroll naar het einde
            self.update() # Forceer GUI update

        # Toon de uiteindelijke resultaten
        self.output_text.insert(tk.END, "\n" + "="*50 + "\n")
        self.output_text.insert(tk.END, "DEFINITIEVE RESULTATEN (Samenvatting per bestand):\n")
        self.output_text.insert(tk.END, json.dumps(all_results, indent=4))
        self.output_text.see(tk.END) # Scroll naar het einde

# Start de applicatie
if __name__ == "__main__":
    app = LogFileAnalyzer()
    app.mainloop()