import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import glob
import os
import statistics
import threading

class LogAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ECG Log Analyzer & Protocol Matcher")
        self.root.geometry("1100x700")

        # Variabelen
        self.log_folder_path = tk.StringVar()
        self.protocol_file_path = tk.StringVar()
        self.protocol_data = {} # Opslag voor {bestandsnaam_stem: target_bpm}

        # --- UI Opbouw ---
        
        # Frame voor selecties
        input_frame = tk.LabelFrame(root, text="Instellingen", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Protocol Index Selectie
        tk.Label(input_frame, text="Selecteer Protocol Index (.jsonl):").grid(row=0, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.protocol_file_path, width=70).grid(row=0, column=1, padx=5)
        tk.Button(input_frame, text="Bladeren...", command=self.select_protocol_file).grid(row=0, column=2)

        # Log Map Selectie
        tk.Label(input_frame, text="Selecteer Log Map:").grid(row=1, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.log_folder_path, width=70).grid(row=1, column=1, padx=5)
        tk.Button(input_frame, text="Bladeren...", command=self.select_log_folder).grid(row=1, column=2)

        # Actie Knop
        self.run_btn = tk.Button(input_frame, text="Start Analyse", command=self.start_analysis, bg="#dddddd", height=2)
        self.run_btn.grid(row=2, column=1, pady=10, sticky="ew")

        # Resultaten Tabel (Treeview)
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("bestand", "versie", "target", "gemiddeld", "laatste_20", "delta", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Kolom instellingen
        self.tree.heading("bestand", text="Bestand (Log)")
        self.tree.column("bestand", width=300)
        self.tree.heading("versie", text="Versie")
        self.tree.column("versie", width=120)
        self.tree.heading("target", text="Doel BPM")
        self.tree.column("target", width=80)
        self.tree.heading("gemiddeld", text="Gem. (na 30s)")
        self.tree.column("gemiddeld", width=100)
        self.tree.heading("laatste_20", text="Gem. (laatste 20)")
        self.tree.column("laatste_20", width=120)
        self.tree.heading("delta", text="Afwijking")
        self.tree.column("delta", width=80)
        self.tree.heading("status", text="Status")
        self.tree.column("status", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        # Status balk
        self.status_var = tk.StringVar()
        self.status_var.set("Klaar voor start.")
        tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor="w").pack(side=tk.BOTTOM, fill="x")

    def select_protocol_file(self):
        filename = filedialog.askopenfilename(filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")])
        if filename:
            self.protocol_file_path.set(filename)

    def select_log_folder(self):
        foldername = filedialog.askdirectory()
        if foldername:
            self.log_folder_path.set(foldername)

    def calculate_bpm_from_protocol(self, protocol_list):
        """
        Berekent BPM op basis van de In/Hold/Uit/Hold tijden.
        Gaat uit van de eerste stap in het protocol die herhalingen heeft.
        """
        try:
            for step in protocol_list:
                # We pakken de eerste stap die daadwerkelijk uitgevoerd wordt of gewoon de eerste als fallback
                t_in = float(step.get("In_s", 0))
                t_hold1 = float(step.get("Hold1_s", 0))
                t_out = float(step.get("Uit_s", 0))
                t_hold2 = float(step.get("Hold2_s", 0))
                
                total_sec = t_in + t_hold1 + t_out + t_hold2
                if total_sec > 0:
                    return 60.0 / total_sec
            return 0.0
        except Exception:
            return 0.0

    def load_protocol_index(self, filepath):
        """Leest de protocol index in en maakt een map van bestandsnaam -> verwachte BPM."""
        self.protocol_data = {}
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        filename = data.get("ecg_log_filename", "")
                        protocol = data.get("protocol", [])
                        
                        if filename and protocol:
                            bpm = self.calculate_bpm_from_protocol(protocol)
                            # We slaan de 'stam' van de bestandsnaam op (zonder .jsonl) om makkelijker te matchen
                            # Origineel: XXX-001_2025... .jsonl -> XXX-001_2025...
                            stem = os.path.splitext(filename)[0]
                            self.protocol_data[stem] = bpm
                            count += 1
                    except json.JSONDecodeError:
                        continue
            return True, f"{count} protocollen geladen."
        except Exception as e:
            return False, str(e)

    def analyze_single_file(self, filepath, target_bpm):
        """
        Analyseert één bestand.
        - Slaat de eerste 30 seconden aan data over.
        - Berekent gemiddelden.
        """
        est_rr_values = []
        version = "Onbekend"
        start_ts = None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Versie info ophalen (vaak in de eerste regels)
                        if "parameters" in data:
                            params = data["parameters"]
                            if "version" in params:
                                version = params["version"]
                        
                        # Tijd bepalen voor de 30s skip
                        current_ts = data.get("ts")
                        if current_ts is not None and isinstance(current_ts, (int, float)):
                            if start_ts is None:
                                start_ts = current_ts
                            
                            # Als we nog binnen de eerste 30 seconden (30000 ms) zitten, overslaan
                            if (current_ts - start_ts) < 30000:
                                continue

                        # Data verzamelen
                        if data.get("signal") == "resp_rr":
                            val = data.get("estRR")
                            if val is not None and isinstance(val, (int, float)):
                                est_rr_values.append(float(val))
                                
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return None, f"Fout: {e}"

        if not est_rr_values:
            return None, "Geen data (na 30s)"

        # Statistieken berekenen
        mean_val = statistics.mean(est_rr_values)
        
        n_last = 20
        last_segment = est_rr_values[-n_last:] if len(est_rr_values) > n_last else est_rr_values
        last_mean = statistics.mean(last_segment)
        
        return {
            "version": version,
            "mean": mean_val,
            "last_mean": last_mean,
            "count": len(est_rr_values)
        }, None

    def start_analysis(self):
        # UI Blokkeren
        self.run_btn.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        
        # Thread starten om GUI niet te bevriezen
        threading.Thread(target=self.run_analysis_logic).start()

    def run_analysis_logic(self):
        p_path = self.protocol_file_path.get()
        l_path = self.log_folder_path.get()

        if not os.path.exists(p_path) or not os.path.exists(l_path):
            messagebox.showerror("Fout", "Controleer of het protocolbestand en de logmap bestaan.")
            self.run_btn.config(state=tk.NORMAL)
            return

        self.status_var.set("Index laden...")
        success, msg = self.load_protocol_index(p_path)
        if not success:
            messagebox.showerror("Fout bij laden index", msg)
            self.run_btn.config(state=tk.NORMAL)
            return

        self.status_var.set("Logbestanden zoeken...")
        pattern = os.path.join(l_path, "*.jsonl")
        log_files = sorted(glob.glob(pattern))

        count_processed = 0
        
        for file_path in log_files:
            filename = os.path.basename(file_path)
            
            # --- MATCHING LOGICA ---
            # We zoeken een bronbestand in de protocol_data waarvan de naam (zonder extensie)
            # voorkomt aan het begin van het verwerkte bestand.
            target_bpm = None
            found_stem = None
            
            for stem, bpm in self.protocol_data.items():
                if filename.startswith(stem):
                    target_bpm = bpm
                    found_stem = stem
                    break
            
            if target_bpm is None:
                # Geen match gevonden in index, overslaan of tonen als 'Onbekend'
                continue

            # Analyse uitvoeren
            result, error = self.analyze_single_file(file_path, target_bpm)
            
            if error:
                self.insert_row(filename, "Error", str(target_bpm), "N/A", "N/A", "N/A", error)
                continue
            
            if result:
                # Bereken afwijking
                delta = result['last_mean'] - target_bpm
                delta_str = f"{delta:+.2f}"
                
                status = ""
                if abs(delta) < 1.0:
                    status = "OK"
                elif abs(delta) > 5.0:
                    status = "AFWIJKING (!)"
                else:
                    status = "Matig"

                self.insert_row(
                    filename,
                    result['version'],
                    f"{target_bpm:.1f}",
                    f"{result['mean']:.1f}",
                    f"{result['last_mean']:.1f}",
                    delta_str,
                    status
                )
                count_processed += 1

        self.status_var.set(f"Klaar. {count_processed} bestanden geanalyseerd en gekoppeld.")
        self.run_btn.config(state=tk.NORMAL)

    def insert_row(self, *args):
        self.root.after(0, lambda: self.tree.insert("", tk.END, values=args))

if __name__ == "__main__":
    root = tk.Tk()
    app = LogAnalyzerApp(root)
    root.mainloop()