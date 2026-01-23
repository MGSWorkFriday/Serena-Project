import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import glob
import os
import statistics
import threading
import platform
import subprocess

class LogAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ECG Log Analyzer & Protocol Matcher")
        # AANPASSING: Venster breder gemaakt (1600px)
        self.root.geometry("1600x900") 

        # --- STIJL INSTELLINGEN ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        # Variabelen
        self.log_folder_path = tk.StringVar()
        self.protocol_file_path = tk.StringVar()
        
        # Instellingen variabelen
        self.skip_seconds_var = tk.StringVar(value="30") 

        # Filters
        self.max_dev_var = tk.StringVar(value="0.1") 
        self.max_sd_last_var = tk.StringVar(value="1.0") 
        self.max_sd_total_var = tk.StringVar(value="1.0") 
        
        self.match_version_var = tk.BooleanVar(value=False)

        self.protocol_data = {}         
        self.protocol_data_short = {}   
        
        self.analysis_results = [] 
        self.filter_vars = {} 
        self.col_map = {} 

        # --- STANDAARD PADEN ---
        default_protocol = r"C:\Serena\NaamBestanden\protocol_index.jsonl"
        self.protocol_file_path.set(default_protocol)

        default_logs = r"D:\Github\nwevrijdag\pythonbleakgui_server\logs"
        self.log_folder_path.set(default_logs)

        # --- CONFIGURATIE KOLOMMEN (AANGEPAST VOOR BREEDTE) ---
        # De getallen hieronder zijn de breedtes in pixels.
        # Totaal komt nu uit op ongeveer 1500-1550 pixels.
        self.columns_config = [
            ("bestand", "Bestand", 420),       # Was 260 -> Flink breder
            ("versie", "Versie", 180),         # Was 110 -> Breder
            ("target", "Target", 70),          # Iets ruimer
            ("gemiddeld", "Gem(Tot)", 80),
            ("delta", "Delta(Tot)", 80),
            ("sd_tot", "SD(Tot)", 80),
            ("laatste_20", "Lst 20", 70),
            ("sd_last", "SD(Last)", 80),
            ("status", "Status", 100),         # Was 80
            ("hb_win", "HB Win", 60),
            ("smooth", "Smooth", 60),
            ("harm_rat", "H. Rat", 60),
            ("bpm_min", "Min", 50),
            ("bpm_max", "Max", 50),
            ("buf_size", "Buff", 50)
        ]

        # --- UI Opbouw ---
        
        # 1. Instellingen Frame
        input_frame = tk.LabelFrame(root, text="Instellingen & Import", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Rij 0: Protocol
        tk.Label(input_frame, text="Protocol Index:").grid(row=0, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.protocol_file_path, width=80).grid(row=0, column=1, padx=5) # Entry ook iets breder
        tk.Button(input_frame, text="Bladeren", command=self.select_protocol_file).grid(row=0, column=2)

        # Rij 1: Logs
        tk.Label(input_frame, text="Log Map:").grid(row=1, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.log_folder_path, width=80).grid(row=1, column=1, padx=5)
        tk.Button(input_frame, text="Bladeren", command=self.select_log_folder).grid(row=1, column=2)

        # Rij 2: Skip parameters
        tk.Label(input_frame, text="Negeer starttijd (sec):").grid(row=2, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.skip_seconds_var, width=10).grid(row=2, column=1, sticky="w", padx=5)

        # Rij 3: Start Button
        self.run_btn = tk.Button(input_frame, text="Start Analyse (Data inladen)", command=self.start_analysis, bg="#dddddd", height=2)
        self.run_btn.grid(row=3, column=1, pady=10, sticky="ew")

        # 2. Global Filter Frame
        filter_frame_global = tk.LabelFrame(root, text="Globale Filters (Max Waarden)", padx=10, pady=5)
        filter_frame_global.pack(fill="x", padx=10)

        # Max Afwijking Input
        tk.Label(filter_frame_global, text="Afwijking (Totaal):").pack(side=tk.LEFT)
        tk.Entry(filter_frame_global, textvariable=self.max_dev_var, width=5).pack(side=tk.LEFT, padx=5)

        # Max SD Total Input
        tk.Label(filter_frame_global, text="SD (Totaal):").pack(side=tk.LEFT, padx=(15, 0))
        tk.Entry(filter_frame_global, textvariable=self.max_sd_total_var, width=5).pack(side=tk.LEFT, padx=5)

        # Max SD Last Input
        tk.Label(filter_frame_global, text="SD (Last 20):").pack(side=tk.LEFT, padx=(15, 0))
        tk.Entry(filter_frame_global, textvariable=self.max_sd_last_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # Match Version Toggle
        chk_match = tk.Checkbutton(filter_frame_global, text="Match Version", 
                                   variable=self.match_version_var)
        chk_match.pack(side=tk.LEFT, padx=15)

        tk.Button(filter_frame_global, text="Force Refresh", command=self.apply_filter).pack(side=tk.LEFT, padx=10)
        
        self.root.bind_all("<KeyRelease>", self.apply_filter)

        # 3. TABEL FRAME (Container)
        table_container = tk.Frame(root, padx=10, pady=5)
        table_container.pack(fill="both", expand=True)

        # A: Filter Rij (De zoekvelden)
        self.filter_row_frame = tk.Frame(table_container)
        self.filter_row_frame.pack(fill="x", anchor="w")

        for idx, (col_code, col_name, px_width) in enumerate(self.columns_config):
            self.col_map[col_code] = idx
            
            # Frame met vaste breedte = kolom breedte
            f = tk.Frame(self.filter_row_frame, width=px_width, height=25)
            f.pack_propagate(False) # Zorg dat frame maat behoudt
            f.pack(side=tk.LEFT, padx=0)
            
            var = tk.StringVar()
            self.filter_vars[col_code] = var
            
            ent = tk.Entry(f, textvariable=var, font=("Arial", 9))
            ent.pack(fill=tk.BOTH, expand=True)

        # B: Treeview (De tabel)
        col_names = [c[0] for c in self.columns_config]
        self.tree = ttk.Treeview(table_container, columns=col_names, show="headings")
        
        for col_code, col_name, px_width in self.columns_config:
            self.tree.heading(col_code, text=col_name)
            # stretch=False is cruciaal om de uitlijning met de filters erboven te behouden
            self.tree.column(col_code, width=px_width, minwidth=px_width, stretch=False)
        
        self.tree.bind("<Double-1>", self.on_double_click)

        # Scrollbars
        vsb = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        # Grid/Pack Layout
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        vsb.pack(side=tk.RIGHT, fill="y")
        hsb.pack(side=tk.BOTTOM, fill="x")

        # Status balk
        self.status_var = tk.StringVar()
        self.status_var.set("Klaar voor start.")
        tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor="w").pack(side=tk.BOTTOM, fill="x")

    # --- EVENT HANDLERS ---
    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection: return
        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        if not values: return
        
        display_name = values[0]
        filename = display_name.replace(" (Soft Match)", "").strip()
        folder = self.log_folder_path.get()
        filepath = os.path.join(folder, filename)
        
        if os.path.exists(filepath):
            try:
                os.startfile(filepath)
            except AttributeError:
                try:
                    if platform.system() == "Darwin": subprocess.call(["open", filepath])
                    else: subprocess.call(["xdg-open", filepath])
                except: pass
        else:
            messagebox.showerror("Fout", f"Bestand niet gevonden: {filepath}")

    # --- HULPFUNCTIES ---
    def select_protocol_file(self):
        current_path = self.protocol_file_path.get()
        start_dir = os.path.dirname(current_path) if os.path.exists(os.path.dirname(current_path)) else os.getcwd()
        filename = filedialog.askopenfilename(initialdir=start_dir, filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")])
        if filename: self.protocol_file_path.set(filename)

    def select_log_folder(self):
        current_dir = self.log_folder_path.get()
        start_dir = current_dir if os.path.exists(current_dir) else os.getcwd()
        foldername = filedialog.askdirectory(initialdir=start_dir)
        if foldername: self.log_folder_path.set(foldername)

    def calculate_bpm_from_protocol(self, protocol_list):
        try:
            for step in protocol_list:
                t = float(step.get("In_s", 0)) + float(step.get("Hold1_s", 0)) + float(step.get("Uit_s", 0)) + float(step.get("Hold2_s", 0))
                if t > 0: return 60.0 / t
            return 0.0
        except: return 0.0

    def load_protocol_index(self, filepath):
        self.protocol_data = {}
        self.protocol_data_short = {} 
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        fn, prot = data.get("ecg_log_filename"), data.get("protocol")
                        if fn and prot:
                            bpm = self.calculate_bpm_from_protocol(prot)
                            stem = os.path.splitext(fn)[0]
                            self.protocol_data[stem] = bpm
                            if "_" in stem:
                                short_id = stem.split("_")[0]
                                self.protocol_data_short[short_id] = bpm
                            count += 1
                    except: continue
            return True, f"{count} protocollen geladen."
        except Exception as e: return False, str(e)

    def analyze_single_file(self, filepath, target_bpm, skip_sec):
        est_rr_values = []
        file_params = {"version":"?","HEARTBEAT_WINDOW":"-","SMOOTH_WIN":"-","HARMONIC_RATIO":"-","BPM_MIN":"-","BPM_MAX":"-","BUFFER_SIZE":"-"}
        start_ts = None
        skip_ms = skip_sec * 1000.0

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        if "parameters" in data:
                            p = data["parameters"]
                            for k in file_params:
                                if k == "version" and "version" in p: file_params[k] = p["version"]
                                elif k in p: file_params[k] = p[k]
                        
                        ts = data.get("ts")
                        if ts is not None and isinstance(ts, (int, float)):
                            if start_ts is None: start_ts = ts
                            if (ts - start_ts) < skip_ms: 
                                continue

                        if data.get("signal") == "resp_rr":
                            val = data.get("estRR")
                            if val is not None and isinstance(val, (int, float)): est_rr_values.append(float(val))
                    except: continue
        except Exception as e: return None, str(e)

        if not est_rr_values: return None, "Geen data"

        # Totaal Statistieken
        total_mean = statistics.mean(est_rr_values)
        total_sd = statistics.stdev(est_rr_values) if len(est_rr_values) > 1 else 0.0

        # Laatste 20 Statistieken
        n_last = 20
        last_segment = est_rr_values[-n_last:] if len(est_rr_values) > n_last else est_rr_values
        last_mean = statistics.mean(last_segment)
        last_sd = statistics.stdev(last_segment) if len(last_segment) > 1 else 0.0
        
        return {
            "params": file_params, 
            "mean": total_mean, 
            "total_sd": total_sd, 
            "last_mean": last_mean, 
            "last_sd": last_sd, 
            "count": len(est_rr_values)
        }, None

    def start_analysis(self):
        self.root.config(cursor="watch")
        self.run_btn.config(state=tk.DISABLED)
        self.status_var.set("Bezig met verwerken...")
        threading.Thread(target=self.run_analysis_logic).start()

    def run_analysis_logic(self):
        self.analysis_results = [] 
        p_path, l_path = self.protocol_file_path.get(), self.log_folder_path.get()
        
        try: skip_sec = float(self.skip_seconds_var.get().replace(',','.'))
        except: skip_sec = 30.0

        def reset_on_error():
            self.root.config(cursor="")
            self.run_btn.config(state=tk.NORMAL)

        if not os.path.exists(p_path) or not os.path.exists(l_path):
            messagebox.showerror("Fout", "Controleer paden.")
            self.root.after(0, reset_on_error)
            return

        self.status_var.set("Index laden...")
        succ, msg = self.load_protocol_index(p_path)
        if not succ:
            messagebox.showerror("Fout", msg)
            self.root.after(0, reset_on_error)
            return

        self.status_var.set("Analyseren...")
        files = sorted(glob.glob(os.path.join(l_path, "*.jsonl")))
        
        for fp in files:
            fn = os.path.basename(fp)
            target = None
            found_stem = None
            match_type = ""
            
            for stem, bpm in self.protocol_data.items():
                if fn.startswith(stem):
                    target, found_stem, match_type = bpm, stem, "Strict"
                    break
            
            if target is None and "_" in fn:
                sid = fn.split("_")[0]
                if sid in self.protocol_data_short:
                    target, found_stem, match_type = self.protocol_data_short[sid], sid, "Soft"
            
            if target is None: continue

            res, err = self.analyze_single_file(fp, target, skip_sec)
            
            disp_name = fn + (" (Soft Match)" if match_type == "Soft" else "")

            if err:
                row = (disp_name, "Error", str(target), "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-")
                self.analysis_results.append({'vals': row, 'delta': 999.0, 'sd_last': 999.0, 'sd_tot': 999.0, 'stem': found_stem, 'version': 'Error'})
            else:
                p = res['params']
                delta = res['mean'] - target
                
                status = "OK" if abs(delta) < 1.0 else ("AFWIJKING (!)" if abs(delta) > 5.0 else "Matig")
                
                row = (
                    disp_name, p['version'], 
                    f"{target:.1f}", 
                    f"{res['mean']:.1f}",       
                    f"{delta:+.2f}",            
                    f"{res['total_sd']:.2f}",   
                    f"{res['last_mean']:.1f}",  
                    f"{res['last_sd']:.2f}",    
                    status,
                    p['HEARTBEAT_WINDOW'], p['SMOOTH_WIN'], p['HARMONIC_RATIO'],
                    p['BPM_MIN'], p['BPM_MAX'], p['BUFFER_SIZE']
                )
                self.analysis_results.append({
                    'vals': row, 
                    'delta': delta, 
                    'sd_last': res['last_sd'],
                    'sd_tot': res['total_sd'],
                    'stem': found_stem, 
                    'version': p['version']
                })

        self.root.after(0, self.finish_analysis)

    def finish_analysis(self):
        self.root.config(cursor="") 
        self.apply_filter()
        self.run_btn.config(state=tk.NORMAL)

    def apply_filter(self, event=None):
        try: limit_dev = float(self.max_dev_var.get().replace(',', '.'))
        except: limit_dev = 9999.0
        
        try: limit_sd_last = float(self.max_sd_last_var.get().replace(',', '.'))
        except: limit_sd_last = 9999.0

        try: limit_sd_tot = float(self.max_sd_total_var.get().replace(',', '.'))
        except: limit_sd_tot = 9999.0

        self.tree.delete(*self.tree.get_children())
        candidates = []
        
        for item in self.analysis_results:
            if round(abs(item['delta']), 2) > limit_dev: continue
            if item['sd_last'] > limit_sd_last: continue
            if item['sd_tot'] > limit_sd_tot: continue

            match_all = True
            for code, var in self.filter_vars.items():
                txt = var.get().lower().strip()
                if not txt: continue
                idx = self.col_map.get(code)
                if idx is not None and txt not in str(item['vals'][idx]).lower():
                    match_all = False; break
            
            if match_all: candidates.append(item)

        final_list = []
        if self.match_version_var.get():
            stems_present = set(i['stem'] for i in candidates)
            coverage = {}
            for i in candidates:
                coverage.setdefault(i['version'], set()).add(i['stem'])
            
            valid_vers = {v for v, s in coverage.items() if stems_present.issubset(s)}
            final_list = [i for i in candidates if i['version'] in valid_vers]
            msg = f"Match Version: {len(valid_vers)} versies dekken {len(stems_present)} bronnen."
        else:
            final_list = candidates
            msg = f"Getoond: {len(final_list)} (Delta: {limit_dev}, SD-Last: {limit_sd_last}, SD-Tot: {limit_sd_tot})"

        for i in final_list: self.tree.insert("", tk.END, values=i['vals'])
        self.status_var.set(msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogAnalyzerApp(root)
    root.mainloop()