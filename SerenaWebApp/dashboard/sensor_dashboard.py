# -*- coding: utf-8 -*-
"""
Desktop-dashboard voor je sensor-server.
Modulaire versie v1.2 (Met Client Launcher)
"""

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import sys
import os
import webbrowser
import subprocess # NIEUWE IMPORT voor het starten van externe scripts

# Importeer onze nieuwe modules
import sensor_config as cfg
import sensor_api as api
from server_manager import ServerManager
from replay_manager import ReplayManager
from ngrok_manager import NgrokManager
from process_killer import ProcessKiller 

class SensorDashboard(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sensor Server Dashboard (Modulair)")
        self.configure(bg="#020617")
        
        # Window grootte
        self.geometry("950x650")

        # --- Logic Managers ---
        self.server_mgr = ServerManager(self.log_msg_threadsafe)
        self.replay_mgr = ReplayManager(self.server_mgr, self.log_msg_threadsafe)
        self.ngrok_mgr = NgrokManager(self.log_msg_threadsafe) 
        self.process_killer = ProcessKiller(self.log_msg_threadsafe, port=cfg.SERVER_PORT) 

        # --- Variabelen ---
        self.file_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.log_folder_var = tk.StringVar(value=cfg.get_default_log_folder())
        
        self.bulk_var = tk.BooleanVar(value=True)
        self.ingest_url_var = tk.StringVar(value=f"{cfg.SERVER_BASE}/ingest")
        
        self.resp_versions_var = tk.StringVar()
        self.all_versions_var = tk.BooleanVar(value=False)

        # UI Opbouw
        self._build_ui()
        self._init_defaults()

        # Bij sluiten venster
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        container = tk.Frame(self, bg="#020617")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Headers
        tk.Label(container, text="Sensor Server Dashboard", font=("Segoe UI", 14, "bold"), fg="#e5e7eb", bg="#020617").pack(anchor="w")
        
        # --- Knoppenrij Server & API ---
        btn_row = tk.Frame(container, bg="#020617")
        btn_row.pack(anchor="w", pady=(10, 10))

        self._btn(btn_row, "🔁 Rotate log", self.on_rotate, "#10b981")
        self._btn(btn_row, "💣 Kill 8000", self.on_kill_process, "#ef4444")
        
        self.btn_start = self._btn(btn_row, "▶ Start server", self.on_start_server, "#10b981")
        self.btn_stop = self._btn(btn_row, "⏹ Stop server", self.on_stop_server, "#374151", state="disabled")
        self._btn(btn_row, "🩺 Health", self.on_health, "#374151")
        
        # NGROK KNOP
        self.btn_ngrok = self._btn(btn_row, "🌐 Start NGROK", self.on_ngrok, "#f97316")

        # NIEUWE KNOP: Start Client GUI
        self._btn(btn_row, "📱 Start Client", self.on_start_client, "#6366f1")

        # RESTART KNOP
        self._btn(btn_row, "🔄 Restart", self.restart_program, "#f59e0b", side="right")


        # --- Input Sectie ---
        self._lbl(container, "--- INPUT (voor Replay) ---", pady=(8,2))
        self._file_picker(container, "Input Bestand:", self.file_var, self.on_pick_file)
        self._file_picker(container, "Input Map:", self.folder_var, self.on_pick_folder, is_folder=True)

        # --- Output Sectie ---
        self._lbl(container, "--- OUTPUT (voor Analyse) ---", pady=(4,2))
        self._file_picker(container, "Log Map:", self.log_folder_var, self.on_pick_log_folder, is_folder=True)

        # --- Versies ---
        v_row = tk.Frame(container, bg="#020617")
        v_row.pack(fill="x", pady=4)
        tk.Checkbutton(v_row, text="Alle versies", variable=self.all_versions_var, command=self._toggle_all_versions,
                       bg="#020617", fg="#e5e7eb", selectcolor="#111827", activebackground="#020617", activeforeground="#e5e7eb").pack(side="left")
        tk.Label(v_row, text="Versies:", bg="#020617", fg="#e5e7eb").pack(side="left", padx=5)
        tk.Entry(v_row, textvariable=self.resp_versions_var, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb").pack(side="left", fill="x", expand=True, padx=5)
        self._btn(v_row, "Kies...", self.on_choose_versions, "#4b5563", compact=True)

        # --- Actie Knoppen ---
        act_row = tk.Frame(container, bg="#020617")
        act_row.pack(fill="x", pady=10)
        
        tk.Checkbutton(act_row, text="Bulk mode", variable=self.bulk_var, bg="#020617", fg="#e5e7eb", selectcolor="#111827", activebackground="#020617", activeforeground="#e5e7eb").pack(side="left")
        tk.Label(act_row, text="URL:", bg="#020617", fg="#e5e7eb").pack(side="left", padx=(10,2))
        tk.Entry(act_row, textvariable=self.ingest_url_var, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb", width=20).pack(side="left")

        self._btn(act_row, "📊 Analyseer Logs", self.on_analyze, "#8b5cf6", side="right")
        self._btn(act_row, "▶ Start Replay", self.on_start_replay, "#2563eb", side="right", padx=(0,8))

        # --- Log Venster ---
        self.status = scrolledtext.ScrolledText(container, height=12, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb", font=("Consolas", 9))
        self.status.pack(fill="both", expand=True)
        self.status.configure(state="disabled")

    # --- UI Helpers ---
    def _btn(self, parent, text, cmd, bg, fg="#e5e7eb", side="left", padx=(0,4), state="normal", compact=False):
        """Compacte knoppen."""
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, relief="flat", 
                      font=("Segoe UI", 9, "bold" if not compact else "normal"), 
                      padx=6 if not compact else 4, 
                      pady=3 if not compact else 1, 
                      state=state)
        b.pack(side=side, padx=padx)
        return b

    def _lbl(self, parent, text, pady=0):
        tk.Label(parent, text=text, fg="#6b7280", bg="#020617", font=("Segoe UI", 8)).pack(anchor="w", pady=pady)

    def _file_picker(self, parent, label, var, cmd, is_folder=False):
        row = tk.Frame(parent, bg="#020617")
        row.pack(fill="x", pady=(0,4))
        tk.Label(row, text=label, width=12, anchor="w", bg="#020617", fg="#e5e7eb").pack(side="left")
        tk.Entry(row, textvariable=var, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb").pack(side="left", fill="x", expand=True, padx=6)
        tk.Button(row, text="📂", command=cmd, bg="#4b5563", fg="#e5e7eb", relief="flat").pack(side="left")

    def _init_defaults(self):
        versions = cfg.load_resp_versions()
        if versions:
            self.resp_versions_var.set(versions[0])
        self.log_msg("Dashboard geladen (v1.2).")

    # --- Logging ---
    def log_msg(self, text):
        if isinstance(text, str) and text.startswith("URL_FOUND:"):
            base_url = text.split(":", 1)[1].strip()
            final_url = f"{base_url}/Serena.html"
            try:
                webbrowser.open_new_tab(final_url)
                self.log_msg(f"[actie] Open URL in browser: {final_url}")
            except Exception as e:
                self.log_msg(f"[fout] Kon browser niet openen: {e}")
            self.log_msg(f"*** Publieke Mobiele Dashboard URL: {final_url} ***")
            self.btn_ngrok.configure(text="🌐 Stop NGROK", bg="#ef4444")
            return 

        self.status.configure(state="normal")
        self.status.insert("end", str(text) + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")
    
    def log_msg_threadsafe(self, text):
        self.after(0, lambda: self.log_msg(text))

    def update_server_btns(self):
        running = self.server_mgr.is_running()
        self.btn_start.configure(state="disabled" if running else "normal")
        self.btn_stop.configure(state="normal" if running else "disabled", bg="#ef4444" if running else "#374151")
        
        if not self.ngrok_mgr.is_running():
            self.btn_ngrok.configure(text="🌐 Start NGROK", bg="#f97316")
        else:
            self.btn_ngrok.configure(text="🌐 Stop NGROK", bg="#ef4444")

    def restart_program(self):
        self.log_msg("Applicatie wordt herstart...")
        self.server_mgr.stop()
        self.ngrok_mgr.stop()
        try:
            self.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            print(f"[fout] Kon niet herstarten: {e}")
            sys.exit(1)

    # --- Event Handlers ---
    def on_close(self):
        self.server_mgr.stop()
        self.ngrok_mgr.stop() 
        self.destroy()

    def on_rotate(self):
        threading.Thread(target=lambda: self.log_msg_threadsafe(api.call_rotate()[1]), daemon=True).start()

    def on_health(self):
        threading.Thread(target=lambda: self.log_msg_threadsafe(api.call_health()[1]), daemon=True).start()
    
    def on_kill_process(self):
        threading.Thread(target=self.process_killer.find_and_kill_process, daemon=True).start()
        self.after(2000, self.update_server_btns)
        
    def on_ngrok(self):
        if self.ngrok_mgr.is_running():
            self.ngrok_mgr.stop()
        else:
            if not self.server_mgr.is_running():
                self.log_msg("[fout] Start eerst de Sensor Server.")
                return
            threading.Thread(target=self.ngrok_mgr.start, daemon=True).start()
        self.update_server_btns()

    def on_start_server(self):
        txt = self.resp_versions_var.get().strip()
        v = txt.split(",")[0].strip() if txt and "*" not in txt else None
        if self.server_mgr.start(version=v):
            self.update_server_btns()

    def on_stop_server(self):
        self.server_mgr.stop()
        self.ngrok_mgr.stop()
        self.update_server_btns()
    
    def on_start_client(self):
        """Start de losse Client GUI (mainGUI.py) in de sibling folder."""
        # 1. Bepaal waar we nu zijn (in .../pythonbleakgui_server/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Ga naar de sibling folder 'pythonbleakgui'
        #    Dit gaat 1 map omhoog (..) en dan pythonbleakgui in.
        target_dir = os.path.abspath(os.path.join(current_dir, "..", "pythonbleakgui"))
        target_script = "mainGUI.py"
        full_path = os.path.join(target_dir, target_script)

        if not os.path.exists(full_path):
            self.log_msg(f"[fout] Kan Client bestand niet vinden op:\n{full_path}")
            return

        try:
            # We gebruiken sys.executable om zeker te zijn dat we dezelfde python versie/env gebruiken.
            # We vervangen python.exe door pythonw.exe als we op Windows zitten om het zwarte scherm te voorkomen.
            exe = sys.executable
            if "python.exe" in exe: 
                exe = exe.replace("python.exe", "pythonw.exe")
            
            # 3. Start het proces met 'cwd=target_dir' (werkt als cd /d ...)
            subprocess.Popen([exe, target_script], cwd=target_dir)
            self.log_msg(f"[actie] Client GUI gestart vanuit: {target_dir}")
        except Exception as e:
            self.log_msg(f"[fout] Kon Client niet starten: {e}")

    def on_start_replay(self):
        folder = self.folder_var.get().strip()
        fpath = self.file_var.get().strip()
        
        if not folder and not fpath:
            self.log_msg("[fout] Geen input gekozen.")
            return

        txt = self.resp_versions_var.get().strip()
        if self.all_versions_var.get() or txt == "*":
            versions = cfg.load_resp_versions()
        else:
            versions = [x.strip() for x in txt.split(",") if x.strip()]
        
        if not versions: versions = [None] 

        self.log_msg(f"[actie] Start replay loop voor {len(versions)} versies...")
        
        if self.server_mgr.is_running():
            self.server_mgr.stop()
            self.update_server_btns()
            self.ngrok_mgr.stop() 

        def run():
            self.replay_mgr.run_versions_loop(versions, folder, fpath, self.ingest_url_var.get(), self.bulk_var.get())
            self.after(0, self.update_server_btns) 

        threading.Thread(target=run, daemon=True).start()

    def on_analyze(self):
        folder = self.log_folder_var.get().strip()
        if not folder:
            self.log_msg("[fout] Geen log map gekozen.")
            return
        threading.Thread(target=lambda: self.replay_mgr.run_analyzer(folder), daemon=True).start()

    # --- Pickers & Dialogs ---
    def on_pick_file(self):
        p = filedialog.askopenfilename(filetypes=[("JSON/L", "*.json *.jsonl")])
        if p: self.file_var.set(p)

    def on_pick_folder(self):
        p = filedialog.askdirectory()
        if p: self.folder_var.set(p)

    def on_pick_log_folder(self):
        p = filedialog.askdirectory()
        if p: self.log_folder_var.set(p)

    def _toggle_all_versions(self):
        if self.all_versions_var.get():
            self.resp_versions_var.set("*")

    def on_choose_versions(self):
        top = tk.Toplevel(self)
        top.configure(bg="#020617")
        top.geometry("300x400")
        lb = tk.Listbox(top, selectmode="multiple", bg="#020617", fg="#e5e7eb")
        lb.pack(fill="both", expand=True)
        
        all_v = cfg.load_resp_versions()
        for v in all_v: lb.insert("end", v)
            
        def ok():
            sel = [all_v[i] for i in lb.curselection()]
            self.resp_versions_var.set(", ".join(sel))
            self.all_versions_var.set(False)
            top.destroy()
            
        tk.Button(top, text="OK", command=ok, bg="#10b981").pack(fill="x")

if __name__ == "__main__":
    try:
        if not hasattr(cfg, 'SERVER_PORT'):
            cfg.SERVER_PORT = 8000 
            cfg.SERVER_BASE = "http://localhost:8000"
    except NameError:
         pass
         
    app = SensorDashboard()
    app.mainloop()