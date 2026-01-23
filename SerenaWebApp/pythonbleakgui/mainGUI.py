# mainGUI.py
# -*- coding: utf-8 -*-
"""
Wearable ECG — Polar H10 (Windows)
Modular Refactor - Performance Fix & Pre-draw Graph + Tabel Usability Fixes
** Aangepast: Auto-scan bij opstarten & Nette disconnect bij afsluiten (X) **
** Update: TargetRR + Breath Cycle + FEEDBACK EDITOR (Custom Buttons ipv Tabs) **
** Update: X-as scrolt nu mee met de tijd (Time Walking) **
** Update: BreathTarget Heartbeat (elke 5s logging + direct bij stop) **
** Update: Device ID nu gebaseerd op NAAM (gelijk aan HTML versie) **
** Update: Techniek naam wordt nu meegestuurd naar server voor parameter-wissel **
"""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import csv
import os
import sys 
import collections
import traceback
import numpy as np
import json
import requests
from datetime import datetime
#from gui_config import open_config_dialog

# Externe libraries
from bleak import BleakScanner
from polar_python import PolarDevice, MeasurementSettings, SettingType, ECGData
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# --- EIGEN MODULES ---
import config
from algorithms import RobustECGHRDetector
from network import IngestClient
from theme import apply_dark_theme
from breathing_logic import calculate_breath_y
import manual_event_api 

from technique_editor import TechniqueEditor # Zorg dat technique_editor.py in dezelfde map staat

# ----------------------------- Globals --------------------------------

loop = None                
polar_device = None        
streaming = False          

# Multi-user identifier
current_device_id = "UNKNOWN"

# Buffers & Detector
ecg_buffer = collections.deque(maxlen=config.SAMPLE_RATE * config.WINDOW_SECONDS)
total_sample_count = 0  

_hrdet = RobustECGHRDetector(sr_hz=config.SAMPLE_RATE)

# Opslag en Logging
save_file = None
csv_writer = None
ecg_field_name = None

# BLE scan
selected_device = None
found_devices = []

# Netwerk
ingest_client = None

# Recording & Status
recording_active = False 
recording_file = None     
breathing_active = False 
current_technique_name = None 

# UI References
btn_start_adem = None
btn_stop_adem = None
btn_start_recording = None
btn_stop_recording = None
btn_save_bestand = None
btn_open_map = None 
alerts_text = None
status_var = None


_running = True 

# Globals voor Adem Animatie & Preview
_anim_running = False
_anim_time = 0.0
_last_tick = None 
_current_row_idx = 0
_row_start_time = 0.0
_repeats_left = 0 
_hist_x, _hist_y, _hist_last_t = [], [], 0.0
_curve_past, _curve_future, _ball_dot, _last_plot_T = None, None, None, 0.0

# Nieuwe global voor de vooraf berekende lijn en snapshot data
_preview_x = []
_preview_y = []
_active_protocol_data = [] 

# -------------------- UI Logging Helpers --------------------------

def _alerts_append(level: str, msg: str):
    if not _running: return
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {level.upper():5s}  {msg}\n"
    def _do():
        if not alerts_text: return
        try:
            alerts_text.configure(state="normal")
            tag = {"info":"info","warn":"warn","error":"error"}.get(level,"info")
            alerts_text.insert("end", line, (tag,))
            alerts_text.see("end")
            alerts_text.configure(state="disabled")
            if status_var: status_var.set(f"{level.upper()}: {msg}")
        except: pass 
    root.after(0, _do)

def ui_info(msg):  _alerts_append("info", msg)
def ui_warn(msg):  _alerts_append("warn", msg)
def ui_error(msg): _alerts_append("error", msg)

def ui_set_text(text):
    def _set():
        try:
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, text)
        except: pass
    root.after(0, _set)

def log_exception(prefix, exc):
    traceback.print_exc()
    ui_error(f"{prefix} {exc}")

# -------------------- Restart Functie -----------------------------

def restart_program():
    """Herstart de huidige Python applicatie."""
    global _running
    ui_info("Applicatie wordt herstart...")
    _running = False
    
    if polar_device and loop and loop.is_running():
        async def quick_disconnect():
            try: await polar_device.disconnect()
            except: pass
        asyncio.run_coroutine_threadsafe(quick_disconnect(), loop)

    try:
        root.destroy()
    except:
        pass
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        print(f"Fout bij herstarten: {e}")
        sys.exit(1)

# -------------------- Feedback Editor (Config) --------------------

# In mainGUI.py

def open_feedback_config():
    """Opent een venster om de feedback regels (Tekst én Audio) te beheren."""
    base_url = ingest_url_var.get().strip()
    if base_url.endswith("/ingest"):
        base_url = base_url[:-7]
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    
    api_url = f"{base_url}/feedback/rules"

    # Haal huidige regels op van server
    try:
        resp = requests.get(api_url, timeout=2)
        resp.raise_for_status()
        current_rules = resp.json()
    except Exception as e:
        messagebox.showerror("Verbindingsfout", f"Kan regels niet ophalen:\n{e}")
        return

    # Huidige instellingen ophalen (of defaults)
    current_settings = current_rules.get("settings", {})
    val_stability = current_settings.get("stability_duration", 3.0)
    val_repeat = current_settings.get("repeat_interval", 12.0)
    val_visual = current_settings.get("visual_interval", 2.0)

    # Bouw Editor Window
    top = tk.Toplevel(root)
    top.title("Feedback & Audio Configuratie")
    top.geometry("1000x700") # Iets hoger gemaakt voor de extra settings
    top.configure(bg='#2e2e2e')

    # --- NIEUW: Algemene Instellingen Frame ---
    settings_frame = ttk.LabelFrame(top, text="Algemene Timers")
    settings_frame.pack(fill=tk.X, padx=10, pady=10)

    # Helper voor invoervelden
    def add_setting_field(parent, label_text, default_val):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(frame, text=label_text).pack(anchor="w")
        var = tk.DoubleVar(value=default_val)
        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.pack(anchor="w")
        return var

    # De 3 nieuwe velden
    var_stab = add_setting_field(settings_frame, "Stabiliteit (sec):", val_stability)
    var_rep  = add_setting_field(settings_frame, "Herhaal Audio (sec):", val_repeat)
    var_vis  = add_setting_field(settings_frame, "Update Scherm (sec):", val_visual)
    
    # Korte uitleg erbij (optioneel)
    info_lbl = ttk.Label(settings_frame, text="(Stabiliteit = hoe lang meting stabiel moet zijn voor spraak)", font=("Arial", 8))
    info_lbl.pack(side=tk.LEFT, padx=20, pady=10)
    # ------------------------------------------

    cat_config = {
        "blue":     ("Start",       "Blue.TButton"),
        "green":    ("Goed",        "Green.TButton"),
        "orange":   ("Let op",      "Orange.TButton"),
        "red_fast": ("Te Snel",     "Red.TButton"),
        "red_slow": ("Te Langzaam", "Red.TButton")
    }

    # Frame voor Categorie Knoppen
    btn_container = ttk.Frame(top)
    btn_container.pack(fill=tk.X, padx=10, pady=10)

    # Container voor de inhoud
    content_container = ttk.Frame(top)
    content_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    editors = {} 
    content_frames = {}

    def show_category(category):
        for frame in content_frames.values():
            frame.pack_forget()
        if category in content_frames:
            content_frames[category].pack(fill=tk.BOTH, expand=True)

    def create_category_ui(category, data):
        label, style_name = cat_config.get(category, (category, "TButton"))
        
        # Tab knop
        btn = ttk.Button(btn_container, text=label, style=style_name, 
                         command=lambda c=category: show_category(c))
        btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        frame = ttk.Frame(content_container)
        content_frames[category] = frame
        
        # --- Threshold Sectie ---
        thresh_frame = ttk.Frame(frame)
        thresh_frame.pack(fill=tk.X, padx=10, pady=10)
        
        thresh_var = tk.StringVar()
        thresh_key = None
        
        if "threshold_sec" in data:
            ttk.Label(thresh_frame, text="Tijdslimiet (sec):").pack(side=tk.LEFT)
            ttk.Entry(thresh_frame, textvariable=thresh_var, width=10).pack(side=tk.LEFT, padx=5)
            thresh_var.set(str(data["threshold_sec"]))
            thresh_key = "threshold_sec"
        elif "threshold_pct" in data:
            ttk.Label(thresh_frame, text="Afwijking grens (%):").pack(side=tk.LEFT)
            ttk.Entry(thresh_frame, textvariable=thresh_var, width=10).pack(side=tk.LEFT, padx=5)
            thresh_var.set(str(data["threshold_pct"]))
            thresh_key = "threshold_pct"
        else:
            ttk.Label(thresh_frame, text="Geen drempelwaarde voor deze categorie.").pack(side=tk.LEFT)

        # --- Lijst Sectie (Treeview) ---
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        cols = ("weight", "text", "audio")
        tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=10)
        
        tree.heading("weight", text="Prio")
        tree.column("weight", width=50, anchor="center")
        tree.heading("text", text="Scherm Tekst")
        tree.column("text", width=350, anchor="w")
        tree.heading("audio", text="Spraak Tekst (Optioneel)")
        tree.column("audio", width=350, anchor="w")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Data vullen
        for msg in data.get("messages", []):
            w = msg.get("weight", 1)
            t = msg.get("text", "")
            a = msg.get("audio_text", "")
            tree.insert("", "end", values=(w, t, a))

        # --- Edit Sectie ---
        add_frame = ttk.Frame(frame)
        add_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Inputs
        ttk.Label(add_frame, text="Prio:").pack(side=tk.LEFT)
        prio_spin = tk.Spinbox(add_frame, from_=1, to=10, width=3)
        prio_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(add_frame, text="Scherm:").pack(side=tk.LEFT)
        text_entry = ttk.Entry(add_frame, width=30)
        text_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(add_frame, text="Spraak:").pack(side=tk.LEFT)
        audio_entry = ttk.Entry(add_frame, width=30)
        audio_entry.pack(side=tk.LEFT, padx=5)

        # --- Interactiviteit ---

        def on_tree_select(event):
            sel_id = tree.selection()
            if not sel_id: return
            
            vals = tree.item(sel_id[0])["values"]
            prio_spin.delete(0, tk.END)
            prio_spin.insert(0, vals[0])
            text_entry.delete(0, tk.END)
            text_entry.insert(0, vals[1])
            audio_entry.delete(0, tk.END)
            if len(vals) > 2:
                audio_entry.insert(0, vals[2])

        tree.bind("<<TreeviewSelect>>", on_tree_select)

        def add_msg():
            w = prio_spin.get()
            t = text_entry.get().strip()
            a = audio_entry.get().strip()
            if t:
                tree.insert("", "end", values=(w, t, a))
                text_entry.delete(0, tk.END)
                audio_entry.delete(0, tk.END)

        def update_msg():
            sel_id = tree.selection()
            if not sel_id:
                messagebox.showwarning("Selectie", "Selecteer eerst een regel om te bewerken.")
                return
            w = prio_spin.get()
            t = text_entry.get().strip()
            a = audio_entry.get().strip()
            if t:
                tree.item(sel_id[0], values=(w, t, a))
            else:
                messagebox.showwarning("Fout", "Schermtekst mag niet leeg zijn.")

        def del_msg():
            sel = tree.selection()
            for item in sel:
                tree.delete(item)

        ttk.Button(add_frame, text="Toevoegen", command=add_msg).pack(side=tk.LEFT, padx=10)
        ttk.Button(add_frame, text="Update Selectie", command=update_msg).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_frame, text="Verwijder", command=del_msg).pack(side=tk.LEFT, padx=5)

        editors[category] = {
            "tree": tree,
            "thresh_var": thresh_var,
            "thresh_key": thresh_key
        }

    order = ["blue", "green", "orange", "red_fast", "red_slow"]
    first_cat = None
    for cat in order:
        if cat in current_rules:
            create_category_ui(cat, current_rules[cat])
            if not first_cat: first_cat = cat

    if first_cat: show_category(first_cat)

    # --- Opslaan Sectie ---
    btm_frame = ttk.Frame(top)
    btm_frame.pack(fill=tk.X, padx=10, pady=10)

    def save_changes():
        new_rules = {}
        
        # 1. Categorieën verwerken
        for cat, widgets in editors.items():
            msgs = []
            for child in widgets["tree"].get_children():
                vals = widgets["tree"].item(child)["values"]
                weight = int(vals[0])
                text = str(vals[1])
                audio_text = str(vals[2]).strip()
                msg_obj = {"weight": weight, "text": text}
                if audio_text: msg_obj["audio_text"] = audio_text
                msgs.append(msg_obj)
            
            cat_obj = {"messages": msgs}
            if widgets["thresh_key"]:
                try:
                    val = float(widgets["thresh_var"].get())
                    cat_obj[widgets["thresh_key"]] = val
                except ValueError:
                    messagebox.showerror("Fout", f"Ongeldige waarde voor {cat} drempel.")
                    return
            new_rules[cat] = cat_obj

        # 2. Algemene instellingen toevoegen (NIEUW)
        try:
            new_rules["settings"] = {
                "stability_duration": var_stab.get(),
                "repeat_interval": var_rep.get(),
                "visual_interval": var_vis.get()
            }
        except ValueError:
            messagebox.showerror("Fout", "Controleer of de timer velden geldige getallen zijn.")
            return

        # 3. Opsturen
        try:
            r = requests.post(api_url, json=new_rules, timeout=3)
            r.raise_for_status()
            messagebox.showinfo("Succes", "Regels en instellingen opgeslagen!")
            top.destroy()
        except Exception as e:
            messagebox.showerror("Opslaan Mislukt", f"Kon niet opslaan:\n{e}")

    ttk.Button(btm_frame, text="Opslaan & Sluiten", style="Green.TButton", command=save_changes).pack(side=tk.RIGHT)
    ttk.Button(btm_frame, text="Annuleren", command=top.destroy).pack(side=tk.RIGHT, padx=10)
    


# -------------------- Polar callbacks (DATA) --------------------------

def on_data(data):
    global csv_writer, save_file, ecg_field_name, ingest_client
    global recording_active, recording_file
    global breathing_active, _active_protocol_data, _current_row_idx 
    global total_sample_count
    global current_device_id

    if isinstance(data, ECGData):
        if ecg_field_name is None:
            for fld in ["data", "microvolts", "samples_uv", "samples", "values", "uV"]:
                if hasattr(data, fld):
                    ecg_field_name = fld
                    ui_info(f"[ECG] samples veld: {ecg_field_name}")
                    break
            if ecg_field_name is None:
                ui_warn("[ECG] onbekend sample-veld")
                return

        try:
            samples_raw = getattr(data, ecg_field_name)
        except Exception as e:
            ui_warn(f"[ECG] kon samples niet lezen: {e}")
            return

        if isinstance(samples_raw, dict):
            samples = None
            for k in ("samples", "microvolts", "values", "uV"):
                if k in samples_raw:
                    samples = samples_raw[k]; break
            if samples is None:
                for v in samples_raw.values():
                    if hasattr(v, "__iter__"):
                        samples = v; break
        else:
            samples = samples_raw

        try:
            samples = list(samples)
        except Exception:
            samples = [int(samples)]

        ecg_buffer.extend(samples)
        total_sample_count += len(samples) 

        ui_set_text(" ".join(str(v) for v in samples))

        ts_any = getattr(data, "timestamp", None)
        if isinstance(ts_any, (int, float)) and ts_any > 1e12:
            ts_ms = int(ts_any / 1_000_000) 
        elif isinstance(ts_any, (int, float)):
            ts_ms = int(ts_any)             
        else:
            ts_ms = int(time.time() * 1000)

        target_rr = None
        breath_cycle = None 

        if breathing_active and _active_protocol_data:
            try:
                if 0 <= _current_row_idx < len(_active_protocol_data):
                    p = _active_protocol_data[_current_row_idx]
                    cycle_duration = p[0] + p[1] + p[2] + p[3]
                    
                    if cycle_duration > 0:
                        target_rr = round(60.0 / cycle_duration, 2)
                    
                    breath_cycle = {
                        "in": p[0], "hold1": p[1], "out": p[2], "hold2": p[3]
                    }
            except Exception:
                pass 

        base_record = {
            "device_id": current_device_id,  # <--- ID meesturen
            "signal": "ecg", 
            "ts": ts_ms
        }
        if target_rr is not None:
            base_record["TargetRR"] = target_rr
        if breath_cycle is not None:
            base_record["breath_cycle"] = breath_cycle
            
        base_record["samples"] = samples

        if csv_writer:
            for s in samples:
                csv_writer.writerow([ts_ms, s])
            save_file.flush()
            
        if recording_active and recording_file is not None:
            try:
                loop.call_soon_threadsafe(
                    lambda: (recording_file.write(json.dumps(base_record) + '\n'), recording_file.flush()) 
                    if recording_file else None
                )
            except Exception as e:
                ui_error(f"[FE-LOG] Fout bij wegschrijven: {e}")
                
        if ingest_client is not None:
            loop.call_soon_threadsafe(asyncio.create_task, ingest_client.add(base_record))

        _hrdet.add_batch(ts_ms, samples)

# --------------------------- Async taken ------------------------------

async def scan_devices():
    global found_devices, selected_device
    ui_info("Scanning 6s… (Filter: Polar)")
    
    devices = await BleakScanner.discover(timeout=6.0)
    
    found_devices = []
    listbox.delete(0, tk.END)
    
    for d in devices:
        name = d.name or ""
        if "polar" in name.lower():
            display_name = d.name or "(unknown)"
            found_devices.append(d)
            listbox.insert(tk.END, f"{display_name} ({d.address})")
            
    ui_info(f"Gevonden: {len(found_devices)} Polar device(s)")

    if len(found_devices) == 1:
        selected_device = found_devices[0]
        listbox.selection_set(0)
        ui_info("Slechts 1 device gevonden, auto-connect...")
        await do_connect()

async def do_connect():
    global polar_device, selected_device, streaming, total_sample_count, current_device_id
    if not selected_device:
        ui_warn("Selecteer een sensor")
        return
    try:
        # --- AANGEPAST: ID via NAAM bepalen (Match met HTML logic) ---
        raw_name = selected_device.name or "UNKNOWN"
        # Verwijder "Polar", "H10", spaties, colons en dashes om een clean ID te krijgen
        clean_name = raw_name.replace("Polar", "").replace("H10", "").strip()
        # Behoud alleen letters en cijfers
        clean_name = "".join(ch for ch in clean_name if ch.isalnum())
        
        current_device_id = clean_name.upper()
        if not current_device_id: 
            current_device_id = "UNKNOWN_ID"

        ui_info(f"Device ID ingesteld (via naam): {current_device_id}")

        total_sample_count = 0 
        polar_device = PolarDevice(selected_device, on_data)
        await polar_device.connect()
        ui_info(f"Verbonden met {selected_device.name or '(unknown)'}.")
        
        ui_info("Even wachten op services...")
        await asyncio.sleep(2.0) 
        
        ecg_settings = MeasurementSettings(
            measurement_type="ECG",
            settings=[
                SettingType(type="SAMPLE_RATE", array_length=1, values=[config.SAMPLE_RATE]),
                SettingType(type="RESOLUTION",  array_length=1, values=[14]),
            ],
        )
        await polar_device.start_stream(ecg_settings)
        streaming = True
        ui_info("ECG stream direct gestart.")
        
    except Exception as e:
        log_exception("Connect/Start error:", e)
        if polar_device:
            await polar_device.disconnect()
            polar_device = None

async def do_disconnect():
    global polar_device, save_file, csv_writer, streaming, ingest_client
    try:
        if ingest_client is not None:
            try:
                await ingest_client.__aexit__(None, None, None)
                ui_info("[INGEST] Gestopt voor disconnect.")
            except Exception as e:
                ui_warn(f"[INGEST] Close fout: {e}")
            ingest_client = None

        if polar_device:
            await polar_device.disconnect()
            polar_device = None
        
        streaming = False
        if save_file:
            save_file.close()
            save_file, csv_writer = None, None
            
        ui_info("Verbinding verbroken & Stream gestopt.")
    except Exception as e:
        log_exception("Disconnect error:", e)

async def start_session():
    global ingest_client
    if not polar_device:
        ui_warn("Eerst verbinden!")
        return
    
    url = ingest_url_var.get().strip()
    if url:
        try:
            ingest_ms = int(ingest_ms_var.get()); ingest_sz = int(ingest_size_var.get())
        except Exception:
            ingest_ms, ingest_sz = config.DEFAULT_BATCH_MS, config.DEFAULT_BATCH_SIZE
        try:
            ingest_client = await IngestClient(
                url, batch_ms=ingest_ms, batch_size=ingest_sz, log_fn=ui_info
            ).__aenter__()
            ui_info("Ingest (Server) gestart.")
        except Exception as e:
            ui_warn(f"Ingest kon niet starten: {e}")
            ingest_client = None
    else:
        ui_warn("Ingest URL is leeg")
        ingest_client = None


async def stop_session():
    global ingest_client
    try:
        if ingest_client is not None:
            await ingest_client.__aexit__(None, None, None)
            ui_info("Ingest (Server) gestopt.")
        else:
            ui_warn("Ingest liep niet.")
    except Exception as e:
        log_exception("Stop Ingest error:", e)
    finally:
        ingest_client = None

# --------------------------- Recording & Opslag ------------------------------

def start_recording():
    global recording_active, recording_file, current_device_id
    if recording_active:
        ui_warn("Opname loopt al.")
        return
    if not breathing_active:
        ui_warn("Start eerst de ademhalingsanimatie.")
        return

    try:
        # Gebruik submap met device_id
        save_dir = config.PROTOCOL_DIR
        if current_device_id and current_device_id != "UNKNOWN":
            save_dir = os.path.join(config.PROTOCOL_DIR, current_device_id)
        os.makedirs(save_dir, exist_ok=True)
        
        # Oude RAW files opschonen in DEZE map
        for filename in os.listdir(save_dir):
            if filename.startswith("ECG_RAW_"):
                filepath = os.path.join(save_dir, filename)
                try:
                    if os.path.isfile(filepath): os.remove(filepath)
                except Exception as e:
                    ui_error(f"Fout verwijderen {filename}: {e}")
        
        now = datetime.now()
        filename = f"ECG_RAW_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"
        filepath = os.path.join(save_dir, filename)
        
        recording_file = open(filepath, 'w', encoding='utf-8')
        recording_active = True
        ui_info(f"Frontend recording gestart: {filename}")
        update_button_states()

    except Exception as e:
        ui_error(f"Fout bij starten recording: {e}")
        recording_active = False

def stop_recording():
    global recording_active, recording_file
    if not recording_active: return
    try:
        if recording_file:
            loop.call_soon_threadsafe(recording_file.close)
            recording_file = None
        recording_active = False
        ui_info("Frontend recording gestopt.")
        update_button_states()
    except Exception as e:
        ui_error(f"Fout bij stoppen recording: {e}")
        recording_active = False
        
def save_to_file_clicked():
    global save_file, csv_writer
    if not streaming:
        ui_warn("Start eerst een sessie!")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not path: return
    try:
        f = open(path, "w", newline="")
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "microvolt"])
        save_file, csv_writer = f, writer
        ui_info(f"Logging naar {os.path.basename(path)} gestart")
    except Exception as e:
        log_exception("File open error:", e)


def on_technique_saved(new_name):
    """Callback wanneer de editor opslaat of verwijdert."""
    global current_technique_name
    
    if new_name is None:
        # Verwijderd
        current_technique_name = None
        techniek_entry.delete(0, tk.END)
        ui_info("Techniek verwijderd.")
        # Zet knop statussen
        btn_openen.configure(state="normal")
    else:
        # Opgeslagen
        current_technique_name = new_name
        techniek_entry.delete(0, tk.END)
        techniek_entry.insert(0, new_name)
        ui_info(f"Techniek '{new_name}' actief.")
        
    # Openen mag altijd, tenzij je dat specifiek wilt blokkeren
    btn_openen.configure(state="normal")


def open_technique_dialog():
    """Toont een lijst met technieken van de server."""
    try:
        r = requests.get(f"http://localhost:8000/techniques", timeout=2)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        messagebox.showerror("Fout", f"Kon technieken niet laden: {e}")
        return

    # Popup voor selectie
    sel_win = tk.Toplevel(root)
    sel_win.title("Open Techniek")
    sel_win.geometry("400x300")
    sel_win.configure(bg='#2e2e2e')

    list_frame = ttk.Frame(sel_win)
    list_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Lijst
    lb = tk.Listbox(list_frame, bg='#3c3c3c', fg='white', borderwidth=0, highlightthickness=0)
    lb.pack(side="left", fill="both", expand=True)
    
    sb = ttk.Scrollbar(list_frame, orient="vertical", command=lb.yview)
    sb.pack(side="right", fill="y")
    lb.configure(yscrollcommand=sb.set)

    for name in data.keys():
        lb.insert(tk.END, name)

    def load_selected():
        sel = lb.curselection()
        if not sel: return
        name = lb.get(sel[0])
        tech_data = data[name]
        
        # Tabel vullen
        protocol = tech_data.get("protocol", [])
        
        # 1. Tabel leegmaken (reset naar nullen)
        for item in table.get_children():
            table.item(item, values=["0", "0", "0", "0", "0", "00:00"])
            
        # 2. Nieuwe data erin
        items = table.get_children()
        for idx, row_data in enumerate(protocol):
            if idx < len(items):
                # row_data is [a, b, c, d, rep]
                # we moeten Totaal herberekenen
                a, b, c, d, rep = row_data
                total = (a+b+c+d)*rep
                vals = [str(x) for x in row_data] + [f"{total//60:02d}:{total%60:02d}"]
                table.item(items[idx], values=vals)
        
        # Update UI velden
        techniek_entry.delete(0, tk.END)
        techniek_entry.insert(0, name)
        
        global current_technique_name
        current_technique_name = name
        
        ui_info(f"Techniek '{name}' geladen.")
        sel_win.destroy()

    ttk.Button(sel_win, text="Laden", command=load_selected).pack(pady=10)


def save_technique_clicked():
    """Verzamelt data en opent de editor."""
    # Data uit tabel schrapen
    protocol_data = []
    for item in table.get_children():
        # Gebruik de interne functie die je al had: _get_row_params
        # Of lees direct:
        vals = table.item(item, "values")
        # Parse naar integers (in, hold1, out, hold2, rep)
        try:
            row = [int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3]), int(vals[4])]
            # Alleen rijen opslaan die iets doen (niet alles 0)
            if sum(row) > 0:
                protocol_data.append(row)
        except: pass
    
    if not protocol_data:
        messagebox.showwarning("Leeg", "Vul eerst de tabel in.")
        return

    # Check of we een bestaande bewerken of nieuwe maken
    # Als het tekstveld leeg is -> Nieuw. Anders -> Bestaand.
    entry_val = techniek_entry.get().strip()
    is_new = (entry_val == "")
    
    # Open Editor
    TechniqueEditor(root, "" if is_new else entry_val, protocol_data, on_technique_saved)


# --------------------------- Protocol Opslaan ------------------------------

def get_next_index():
    index = 1
    if os.path.exists(config.INDEX_FILE):
        try:
            with open(config.INDEX_FILE, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if 'index' in record and record['index'] >= index:
                            index = record['index'] + 1
                    except json.JSONDecodeError: pass
        except Exception: pass
    return index

def save_protocol_data():
    global _active_protocol_data, current_device_id
    name = name_entry.get().strip() or "OnbekendeNaam"
    try:
        # AANGEPAST: Submap logica
        save_dir = config.PROTOCOL_DIR
        if current_device_id and current_device_id != "UNKNOWN":
            save_dir = os.path.join(config.PROTOCOL_DIR, current_device_id)
        os.makedirs(save_dir, exist_ok=True)
        
        index_file_path = os.path.join(save_dir, "index.jsonl")
        
        # Functie voor locale index
        def get_local_index(path):
            idx = 1
            if os.path.exists(path):
                with open(path,'r') as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            if rec.get('index',0) >= idx: idx = rec['index'] + 1
                        except: pass
            return idx

        current_index = get_local_index(index_file_path)
        protocol_data = []

        if _active_protocol_data:
            for row in _active_protocol_data:
                a, b, c, d, rep = row
                total_sec = (a + b + c + d) * rep
                total_str = f"{total_sec//60:02d}:{total_sec%60:02d}"
                protocol_data.append({
                    "In_s": str(a), "Hold1_s": str(b), "Uit_s": str(c), 
                    "Hold2_s": str(d), "Herhaling": str(rep), "Totaal_tijd": total_str
                })
            ui_info("Protocol opgeslagen vanuit snapshot.")
        else:
            for item_id in table.get_children():
                vals = list(table.item(item_id, "values"))
                protocol_data.append({
                    "In_s": vals[0], "Hold1_s": vals[1], "Uit_s": vals[2], 
                    "Hold2_s": vals[3], "Herhaling": vals[4], "Totaal_tijd": vals[5]
                })
            ui_info("Protocol opgeslagen vanuit tabel.")

        now = datetime.now()
        index_filename_base = f"{name}-{current_index:03d}_{now.strftime('%Y%m%d_%H%M%S')}"
        ecg_log_filename = ""
        
        # Zoek naar RAW files in de save_dir
        raw_files = [
            os.path.join(save_dir, f) for f in os.listdir(save_dir)
            if f.startswith("ECG_RAW_")
        ]
        if raw_files:
            raw_files.sort(key=os.path.getmtime)
            latest_raw_path = raw_files[-1]
            new_raw_filename = f"{index_filename_base}.jsonl" 
            try:
                os.rename(latest_raw_path, os.path.join(save_dir, new_raw_filename))
                ecg_log_filename = new_raw_filename
                ui_info(f"Raw log hernoemd naar: {new_raw_filename}")
            except Exception as e:
                ui_error(f"Fout hernoemen: {e}")
        else:
            ui_warn("Geen raw log gevonden.")
        
        index_record = {
            "index": current_index,
            "timestamp": now.isoformat(),
            "ecg_log_filename": ecg_log_filename,
            "naam": name,
            "protocol": protocol_data,
            "device_id": current_device_id # <--- AANGEPAST
        }
        with open(index_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(index_record) + '\n')
        ui_info(f"Protocol (Index {current_index}) opgeslagen.")
        update_button_states()
    except Exception as e:
        log_exception(f"Fout bij opslaan:", e)

# --------------------------- Open Map (Historie) -----------------------

def open_session_history_window():
    top = tk.Toplevel(root)
    top.title("Opgeslagen sessies")
    top.geometry("900x500")
    top.configure(bg='#2e2e2e') 

    frame_list = ttk.Frame(top)
    frame_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    frame_btns = ttk.Frame(top)
    frame_btns.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

    cols = ("index", "datum", "tijd", "bestand")
    tree = ttk.Treeview(frame_list, columns=cols, show="headings", selectmode="browse")
    tree.heading("index", text="Index"); tree.column("index", width=50, anchor="center")
    tree.heading("datum", text="Datum"); tree.column("datum", width=100, anchor="center")
    tree.heading("tijd", text="Tijd"); tree.column("tijd", width=80, anchor="center")
    tree.heading("bestand", text="Bestandsnaam"); tree.column("bestand", width=400, anchor="w")
    
    scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # AANGEPAST: Bepaal juiste pad
    save_dir = config.PROTOCOL_DIR
    if current_device_id and current_device_id != "UNKNOWN":
        save_dir = os.path.join(config.PROTOCOL_DIR, current_device_id)
    index_file = os.path.join(save_dir, "index.jsonl")

    if os.path.exists(index_file):
        try:
            records = []
            with open(index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try: records.append(json.loads(line.strip()))
                    except json.JSONDecodeError: pass
            for rec in reversed(records):
                idx = rec.get("index", "?")
                raw_ts = rec.get("timestamp", "")
                fname = rec.get("ecg_log_filename", "")
                datum_str = ""
                tijd_str = ""
                try:
                    dt = datetime.fromisoformat(raw_ts)
                    datum_str = dt.strftime("%Y-%m-%d")
                    tijd_str = dt.strftime("%H:%M:%S")
                except: datum_str = raw_ts 
                tree.insert("", "end", values=(idx, datum_str, tijd_str, fname))
        except Exception as e:
            ui_error(f"Fout bij lezen historie: {e}")

    btn_delete = ttk.Button(frame_btns, text="Verwijderen", style='Red.TButton', command=lambda: None)
    btn_delete.pack(pady=5, anchor="n")

# --------------------------- GUI Helpers ------------------------------

def run_async_task(coro):
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    def _done(f):
        try: f.result()
        except Exception as e: log_exception("Async error:", e)
    fut.add_done_callback(_done)

def scan_clicked(): run_async_task(scan_devices())
def connect_clicked(): run_async_task(do_connect())
def disconnect_clicked(): run_async_task(do_disconnect())
def start_clicked(): run_async_task(start_session())
def stop_clicked(): run_async_task(stop_session())

def on_inhale_marker():
    url = ingest_url_var.get()
    if not url: return
    threading.Thread(target=lambda: manual_event_api.send_inhale_marker(url), daemon=True).start()

def clear_alerts():
    alerts_text.configure(state="normal")
    alerts_text.delete("1.0", "end")
    alerts_text.configure(state="disabled")
    status_var.set("Ready")

# --------------------------- Plotting (UPDATED X-AS) ---------------------

def update_plot():
    if not _running: return
    if len(ecg_buffer) < 2:
        root.after(200, update_plot)
        return

    # Data ophalen uit deque
    arr = np.array(list(ecg_buffer))

    # --- NIEUWE LOGICA VOOR SCROLLENDE X-AS ---
    # t_end = totale tijd sinds start connectie (in seconden)
    t_end = total_sample_count / config.SAMPLE_RATE
    
    # duration_in_buffer = hoeveel seconden zitten er NU in de buffer
    duration_in_buffer = len(arr) / config.SAMPLE_RATE
    
    # t_start = beginpunt van de data die nu in de buffer zit
    t_start = t_end - duration_in_buffer
    
    # X-as array maken
    x = np.linspace(t_start, t_end, len(arr))
    
    # View window instellen: [huidige_tijd - venster, huidige_tijd]
    x_lim = (max(0.0, t_end - config.DISPLAY_SECONDS), max(config.DISPLAY_SECONDS, t_end))

    ax.clear()
    ax.set_title(f"Live ECG ({current_device_id})", color='white') # <--- ID in titel
    ax.set_xlabel("Tijd (s)", color='white')
    ax.set_ylabel("Amplitude (µV)", color='white')
    ax.plot(x, arr, color='cyan', linewidth=0.5)
    ax.set_xlim(x_lim) # Dit zorgt voor het 'scrol' effect
    ax.grid(True, alpha=0.5, color='gray')

    if rr_display_var.get():
        rr_list = _hrdet.rr_list_ms(200)
        if len(rr_list) >= 2:
            rr_times_ms = _hrdet.peak_times_ms[-len(rr_list):]
            # Let op: dit kan afwijken van de X-as als rr_times_ms absolute timestamps zijn
            rr_times_s = np.array(rr_times_ms) / 1000.0
            rr_bpm = [60000.0/r for r in rr_list]
            ax2.clear()
            ax2.set_ylabel("HR (BPM)", color='red')
            ax2.plot(rr_times_s, rr_bpm, color='red', marker='.', linestyle='None')
            ax2.set_ylim([40, 180])
            ax2.tick_params(axis='y', labelcolor='red')
            ax2.set_xlim(x_lim)
    else:
        ax2.clear()
    canvas.draw()
    root.after(200, update_plot)

# ---------------------- Adem-animatie & Preview ----------------------

def generate_preview_data(protocol_data, duration=300.0, step=0.05):
    if not protocol_data: return [], []
    rows_data = protocol_data
    total_protocol_time = sum([(r[0]+r[1]+r[2]+r[3])*r[4] for r in rows_data])
    if total_protocol_time <= 0: return [], []

    xs, ys = [], []
    t = 0.0
    row_idx = 0
    while t < duration:
        cycle_idx = row_idx % len(rows_data)
        a, b, c, d, rep = rows_data[cycle_idx]
        T = a + b + c + d
        if T <= 0 or rep <= 0:
            row_idx += 1
            continue
        for _ in range(rep):
            if t >= duration: break
            cycle_ts = np.arange(0, T, step)
            for dt in cycle_ts:
                y = calculate_breath_y(dt, a, b, c, d)
                xs.append(t + dt)
                ys.append(y)
            t += T
        row_idx += 1
    return xs, ys

# --- UPDATED: Functie voor BreathTarget events & heartbeat ---
def send_breath_update():
    """Stuur bericht naar ingest server. 
       Als breathing_active = True -> Stuur Data.
       Als breathing_active = False -> Stuur 'TargetRR': 0 (logging dat het uit staat).
    """
    global ingest_client, _active_protocol_data, _current_row_idx, breathing_active, current_device_id
    
    if ingest_client is None: return 
    
    ts = int(time.time() * 1000)
    
    # 1. Situatie: Ademhaling staat UIT (of net gestopt)
    if not breathing_active or not _active_protocol_data:
        msg = {
            "device_id": current_device_id, # <--- AANGEPAST
            "signal": "BreathTarget",
            "ts": ts,
            "TargetRR": 0
        }
        loop.call_soon_threadsafe(asyncio.create_task, ingest_client.add(msg))
        return

    # 2. Situatie: Ademhaling staat AAN
    try:
        if 0 <= _current_row_idx < len(_active_protocol_data):
            p = _active_protocol_data[_current_row_idx]
            # p = [in, hold1, out, hold2, reps]
            cycle_duration = p[0] + p[1] + p[2] + p[3]
            target_rr = 0.0
            if cycle_duration > 0:
                target_rr = round(60.0 / cycle_duration, 2)

            msg = {
                "device_id": current_device_id, # <--- AANGEPAST
                "signal": "BreathTarget",
                "ts": ts,
                "TargetRR": target_rr,
                "breath_cycle": {
                    "in": p[0], "hold1": p[1], "out": p[2], "hold2": p[3]
                }
            }
            loop.call_soon_threadsafe(asyncio.create_task, ingest_client.add(msg))
    except Exception as e:
        ui_warn(f"Kon breath update niet sturen: {e}")

async def breath_keepalive():
    """Achtergrond taak die elke 5 seconden de BreathTarget status logt."""
    while _running:
        try:
            # We roepen de sync functie aan, die plant de netwerk-taak in
            send_breath_update()
        except Exception:
            pass
        await asyncio.sleep(5.0)

# -------------------------------------------------------------

# --- NIEUW: Helper voor Techniek Wissel Signaal ---
def send_control_packet(active: bool):
    """
    Stuurt een eenmalig BreathTarget commando naar de server om de
    techniek (en bijbehorende parameters) te activeren of deactiveren.
    """
    global ingest_client, current_device_id, _active_protocol_data, _current_row_idx
    
    # Als er geen actieve ingest client is, kunnen we niks sturen
    if ingest_client is None: 
        return

    ts = int(time.time() * 1000)
    
    if active:
        # Haal de naam uit het tekstveld (of de variabele die we tracken)
        technique_name = techniek_name_var.get() 
        
        # Bereken target RR (zoals je al deed in send_breath_update)
        target_rr = 0.0
        cycle_data = None
        
        if _active_protocol_data and 0 <= _current_row_idx < len(_active_protocol_data):
             p = _active_protocol_data[_current_row_idx]
             cycle_duration = p[0] + p[1] + p[2] + p[3]
             if cycle_duration > 0:
                 target_rr = round(60.0 / cycle_duration, 2)
             cycle_data = {
                 "in": p[0], "hold1": p[1], "out": p[2], "hold2": p[3]
             }

        payload = {
            "device_id": current_device_id,
            "signal": "BreathTarget",
            "ts": ts,
            "TargetRR": target_rr,
            "technique": technique_name,  # <--- DIT ZORGT VOOR DE WISSEL OP SERVER
            "breath_cycle": cycle_data
        }
    else:
        # Stop signaal
        payload = {
            "device_id": current_device_id,
            "signal": "BreathTarget",
            "ts": ts,
            "TargetRR": 0,
            "technique": None 
        }

    # Stuur async taak naar de event loop
    loop.call_soon_threadsafe(asyncio.create_task, ingest_client.add(payload))
    ui_info(f"[CONTROL] Techniek wissel verstuurd: {technique_name if active else 'STOP'}")

# -------------------------------------------------------------

def breath_start():
    global _anim_running, _last_tick, _anim_time, breathing_active
    global _current_row_idx, _row_start_time, _repeats_left
    global _hist_x, _hist_y, _hist_last_t, _last_plot_T
    global _preview_x, _preview_y, _active_protocol_data
    
    try: recompute_totals()
    except: pass
    
    items = table.get_children()
    _active_protocol_data = []
    for item in items:
        _active_protocol_data.append(_get_row_params(item))

    _preview_x, _preview_y = generate_preview_data(_active_protocol_data, duration=600.0)
    
    _anim_running = True
    _anim_time = 0.0
    _current_row_idx = 0
    _row_start_time = 0.0
    _repeats_left = 0
    _last_plot_T = -1.0 
    breathing_active = True 
    _hist_x, _hist_y = [], []
    _hist_last_t = 0.0
    _last_tick = time.monotonic()
    
    ui_info("Adem-animatie gestart (Looping & Snapshot)")
    
    # Direct update sturen MET technieknaam (parameter switch)
    send_control_packet(active=True)
    
    update_button_states()
    update_breath_plot()

def breath_stop():
    global _anim_running, _last_tick, breathing_active
    _anim_running = False
    _last_tick = None
    breathing_active = False
    
    # Direct 'TargetRR: 0' sturen MET techniek reset
    send_control_packet(active=False)
    
    ui_info("Adem-animatie gestopt")
    update_button_states()

def update_button_states():
    global breathing_active, recording_active, current_device_id
    if not all([btn_start_adem, btn_stop_adem, btn_start_recording, btn_stop_recording, btn_save_bestand]): return
    
    raw_exists = False
    try: 
        # AANGEPAST: Submap check
        sd = config.PROTOCOL_DIR
        if current_device_id and current_device_id != "UNKNOWN":
            sd = os.path.join(sd, current_device_id)
        if os.path.exists(sd):
            raw_exists = any(f.startswith("ECG_RAW_") for f in os.listdir(sd))
    except: pass

    if recording_active:
        btn_start_adem.configure(state='disabled')
        btn_stop_adem.configure(state='disabled')
        btn_start_recording.configure(state='disabled')
        btn_stop_recording.configure(state='enabled')
    else:
        btn_start_adem.configure(state='disabled' if breathing_active else 'enabled')
        btn_stop_adem.configure(state='enabled' if breathing_active else 'disabled')
        btn_start_recording.configure(state='enabled' if breathing_active else 'disabled')
        btn_stop_recording.configure(state='disabled')
    btn_save_bestand.configure(state='enabled' if (not recording_active and raw_exists) else 'disabled')

# --------------------------- UI Opbouw --------------------------------

root = tk.Tk()
root.title("Wearable ECG & Breathing Coach (Multi-User)")
status_var = tk.StringVar(value="Ready")
rr_display_var = tk.BooleanVar(value=False)

style = ttk.Style()
style.configure("Orange.TButton", background="#f39c12", foreground="white")
style.map("Orange.TButton", background=[('active', '#e67e22')], foreground=[('active', 'white')])

top_frame = ttk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X)
ttk.Button(top_frame, text="Scan", style='Blue.TButton', command=scan_clicked).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(top_frame, text="Connect", style='Green.TButton', command=connect_clicked).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(top_frame, text="Disconnect", style='Red.TButton', command=disconnect_clicked).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(top_frame, text="🌬️ Inademing", command=lambda: root.after(0, on_inhale_marker)).pack(side=tk.LEFT, padx=5, pady=5) 
# -- NIEUWE KNOP --
ttk.Button(top_frame, text="Feedback Config", command=open_feedback_config).pack(side=tk.LEFT, padx=5, pady=5)
# -----------------
ttk.Button(top_frame, text="Start Ingest", style='Green.TButton', command=start_clicked).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(top_frame, text="Stop Ingest", style='Red.TButton', command=stop_clicked).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(top_frame, text="Restart", style='Orange.TButton', command=restart_program).pack(side=tk.RIGHT, padx=5, pady=5)
ttk.Button(top_frame, text="Clear Alerts", command=clear_alerts).pack(side=tk.RIGHT, padx=5, pady=5)

rr_frame = ttk.Frame(top_frame)
rr_frame.pack(side=tk.RIGHT, padx=10, pady=5)
ttk.Checkbutton(rr_frame, text="Show RR (BPM)", variable=rr_display_var).pack(side=tk.LEFT)
log_frame = ttk.Frame(top_frame)
log_frame.pack(side=tk.RIGHT, padx=10, pady=5)
ttk.Button(log_frame, text="Save to File...", command=save_to_file_clicked).pack(side=tk.LEFT)

ingest_url_var = tk.StringVar(value=config.DEFAULT_INGEST_URL)
ingest_ms_var = tk.StringVar(value=str(config.DEFAULT_BATCH_MS))
ingest_size_var = tk.StringVar(value=str(config.DEFAULT_BATCH_SIZE))

ingest_frame = ttk.LabelFrame(root, text="HTTP Ingest")
ingest_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
ttk.Label(ingest_frame, text="URL:").pack(side=tk.LEFT, padx=5)
ttk.Entry(ingest_frame, textvariable=ingest_url_var, width=30).pack(side=tk.LEFT, padx=2)

split = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
split.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
listbox_frame = ttk.Frame(split, width=200)
listbox = tk.Listbox(listbox_frame)
listbox.bind('<<ListboxSelect>>', lambda e: globals().update(selected_device=found_devices[listbox.curselection()[0]]) if listbox.curselection() else None)
listbox.pack(fill=tk.BOTH, expand=True)
split.add(listbox_frame)
text_box = tk.Text(split, width=34)
split.add(text_box)
fig, ax = plt.subplots(figsize=(10, 3))
ax2 = ax.twinx()
canvas = FigureCanvasTkAgg(fig, master=split)
split.add(canvas.get_tk_widget())

alerts_frame = ttk.Frame(root)
alerts_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6,0))
alerts_text = tk.Text(alerts_frame, height=8, state="disabled")
alerts_text.pack(fill=tk.BOTH, expand=True)
status_bar = ttk.Frame(root)
status_bar.pack(fill=tk.X, padx=6, pady=6)
ttk.Label(status_bar, textvariable=status_var).pack(side=tk.LEFT)

table_frame = ttk.Frame(root)
table_frame.pack(side=tk.LEFT, anchor="sw", padx=10, pady=(0,10))

# 1. Header Frame
header_frame = ttk.Frame(table_frame)
header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

techniek_name_var = tk.StringVar()

def clear_technique():
    """Maakt het veld leeg en reset de tabel."""
    global current_technique_name
    current_technique_name = None
    techniek_name_var.set("") 
    for item in table.get_children():
        table.item(item, values=["0", "0", "0", "0", "0", "00:00"])
    ui_info("Nieuwe techniek gestart (leeg).")
    try: recompute_totals()
    except: pass

def check_entry_state(*args):
    text_val = techniek_name_var.get().strip()
    if btn_openen: btn_openen.configure(state='normal')
    if btn_opslaan: btn_opslaan.configure(state='normal')
    if btn_clear:
        if text_val:
            btn_clear.configure(state='normal')
        else:
            btn_clear.configure(state='disabled')

techniek_name_var.trace_add("write", check_entry_state)

techniek_entry = ttk.Entry(header_frame, width=30, textvariable=techniek_name_var)
techniek_entry.pack(side=tk.LEFT, padx=(0, 2))
btn_clear = ttk.Button(header_frame, text="X", width=3, command=clear_technique)
btn_clear.pack(side=tk.LEFT)
btn_openen = ttk.Button(header_frame, text="Openen", command=open_technique_dialog, width=8)
btn_openen.pack(side=tk.RIGHT)
btn_opslaan = ttk.Button(header_frame, text="Opslaan", command=save_technique_clicked, width=8)
btn_opslaan.pack(side=tk.RIGHT, padx=(0, 5))
check_entry_state()

cols = ["In (s)", "Hold1 (s)", "Uit (s)", "Hold2 (s)", "Herhaling", "Totaal"]
table = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
for col in cols:
    table.heading(col, text=col)
    table.column(col, width=70, anchor="center")
for _ in range(10): table.insert("", "end", values=["0", "0", "0", "0", "0", "00:00"])
table.pack(side=tk.LEFT, fill=tk.Y)

name_control_frame = ttk.Frame(root)
name_control_frame.pack(side=tk.LEFT, anchor="nw", padx=10, pady=(0,10), fill=tk.Y)
ttk.Label(name_control_frame, text="Naam:").pack(pady=(5, 2), anchor="w")
name_entry = ttk.Entry(name_control_frame, width=20)
name_entry.pack(pady=(0, 10), fill=tk.X)
btn_start_adem = ttk.Button(name_control_frame, text="Start Adem", style='Green.TButton', command=breath_start)
btn_start_adem.pack(pady=2, fill=tk.X)
btn_stop_adem = ttk.Button(name_control_frame, text="Stop Adem", style='Red.TButton', command=breath_stop)
btn_stop_adem.pack(pady=2, fill=tk.X)
btn_start_recording = ttk.Button(name_control_frame, text="Start recording", style='Green.TButton', command=start_recording)
btn_start_recording.pack(pady=(15, 2), fill=tk.X)
btn_stop_recording = ttk.Button(name_control_frame, text="Stop recording", style='Red.TButton', command=stop_recording)
btn_stop_recording.pack(pady=2, fill=tk.X)
btn_save_bestand = ttk.Button(name_control_frame, text="Save bestand", style='Blue.TButton', command=save_protocol_data)
btn_save_bestand.pack(pady=(15, 2), fill=tk.X)
btn_open_map = ttk.Button(name_control_frame, text="Open map", style='Orange.TButton', command=open_session_history_window)
btn_open_map.pack(pady=2, fill=tk.X)

breath_frame = ttk.Frame(root)
breath_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10), pady=(0,10))
breath_fig, breath_ax = plt.subplots(figsize=(6, 1.8))
ax2_breath = breath_ax.twinx()
breath_canvas = FigureCanvasTkAgg(breath_fig, master=breath_frame)
breath_widget = breath_canvas.get_tk_widget()
breath_widget.pack(fill=tk.BOTH, expand=True)

_current_edit = {"item": None, "col": None, "entry": None}

def _parse_int0(s):
    try: return max(0, int(str(s).strip()))
    except: return 0

def _get_row_params(item_id):
    vals = table.item(item_id, "values")
    return tuple(_parse_int0(vals[i]) for i in range(5))

def recompute_totals():
    for item in table.get_children():
        a,b,c,d,rep = _get_row_params(item)
        total = (a+b+c+d) * rep
        vals = list(table.item(item, "values"))
        vals[5] = f"{total//60:02d}:{total%60:02d}"
        table.item(item, values=vals)
recompute_totals()

def _begin_edit(item_id, col_index):
    if col_index > 4: return 
    bbox = table.bbox(item_id, column=cols[col_index])
    if not bbox: return
    entry = tk.Entry(table)
    entry.insert(0, table.item(item_id, "values")[col_index])
    entry.select_range(0, tk.END) 
    entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
    entry.focus()
    _current_edit.update(item=item_id, col=col_index, entry=entry)
    entry.bind("<Return>", lambda e: _commit_edit(1))
    entry.bind("<FocusOut>", lambda e: _commit_edit(0))
    entry.bind("<Tab>", lambda e: (_commit_edit(1), "break")[-1]) 
    entry.bind("<Shift-Tab>", lambda e: (_commit_edit(-1), "break")[-1]) 

def _commit_edit(advance=1):
    if _current_edit["entry"] is None: return
    entry = _current_edit["entry"]
    item_id = _current_edit["item"]
    col = _current_edit["col"]
    val = entry.get()
    try: val = str(max(0, int(val)))
    except ValueError: val = "0"
    vals = list(table.item(item_id, "values"))
    vals[col] = val
    table.item(item_id, values=vals)
    entry.destroy()
    _current_edit.update(entry=None)
    recompute_totals()
    if advance != 0:
        items = table.get_children()
        try: cur_idx = items.index(item_id)
        except ValueError: return
        next_col = col + advance
        next_row_idx = cur_idx
        num_cols = 5 
        num_rows = len(items)
        if next_col >= num_cols: 
            next_col = 0
            next_row_idx = (cur_idx + 1) % num_rows
        elif next_col < 0: 
            next_col = num_cols - 1 
            next_row_idx = (cur_idx - 1 + num_rows) % num_rows 
        next_item_id = items[next_row_idx]
        _begin_edit(next_item_id, next_col)

table.bind("<Double-1>", lambda e: _begin_edit(table.identify_row(e.y), int(table.identify_column(e.x)[1:])-1) if table.identify_row(e.y) else None)

def _ensure_row_ready():
    global _current_row_idx, _row_start_time, _repeats_left, _hist_last_t
    global _active_protocol_data 
    if not _active_protocol_data: return False
    max_guard = len(_active_protocol_data)
    while max_guard > 0:
        a,b,c,d,rep = _active_protocol_data[_current_row_idx]
        if rep > 0 and (a+b+c+d) > 0:
            if _repeats_left <= 0:
                _repeats_left = rep
                _row_start_time = _anim_time
                _hist_last_t = _anim_time
            return True
        _current_row_idx = (_current_row_idx + 1) % len(_active_protocol_data)
        _repeats_left = 0
        max_guard -= 1
    return False

def _advance_if_needed(now_anim):
    global _current_row_idx, _row_start_time, _repeats_left
    global _active_protocol_data
    a,b,c,d,rep = _active_protocol_data[_current_row_idx]
    T = a+b+c+d
    if T <= 0: return
    elapsed = now_anim - _row_start_time
    while elapsed >= T and T > 0:
        _repeats_left -= 1
        _row_start_time += T
        elapsed -= T
        if _repeats_left <= 0:
            _current_row_idx = (_current_row_idx + 1) % len(_active_protocol_data)
            _repeats_left = 0
            if not _ensure_row_ready(): break
            send_breath_update()

def update_breath_plot():
    global _last_tick, _anim_time, _hist_x, _hist_y, _hist_last_t
    global _curve_past, _curve_future, _ball_dot, _last_plot_T
    global _current_row_idx, _row_start_time, _repeats_left 
    global _active_protocol_data 
    if not _running: return
    window = 15.0
    now_wall = time.monotonic()
    if _anim_running and _last_tick:
        _anim_time += (now_wall - _last_tick)
    _last_tick = now_wall
    now_anim = _anim_time
    if not _ensure_row_ready():
        has_data = any(sum(row[:4]) > 0 for row in _active_protocol_data)
        if has_data:
            _anim_time = 0.0
            now_anim = 0.0
            _current_row_idx = 0
            _row_start_time = 0.0
            _repeats_left = 0
            _ensure_row_ready()
            send_breath_update()
        else:
            breath_ax.clear()
            _curve_past, _curve_future, _ball_dot, _last_plot_T = None, None, None, 0.0
            breath_ax.set_ylim(-1.2, 1.2)
            breath_ax.grid(True, alpha=0.25, color='gray')
            apply_dark_theme(root, listbox, text_box, alerts_text, [fig, breath_fig], [ax, ax2, breath_ax, ax2_breath])
            breath_canvas.draw()
            root.after(40, update_breath_plot)
            return
    _advance_if_needed(now_anim)
    if not _active_protocol_data: return
    a,b,c,d,rep = _active_protocol_data[_current_row_idx]
    T_active = a+b+c+d
    if _curve_past is None: 
        breath_ax.clear()
        apply_dark_theme(root, listbox, text_box, alerts_text, [fig, breath_fig], [ax, ax2, breath_ax, ax2_breath])
        breath_ax.set_ylim(-1.2, 1.2)
        breath_ax.grid(True, alpha=0.25, color='gray')
        _curve_past, = breath_ax.plot([], [], linewidth=1.5, color='cyan', zorder=2)
        _ball_dot = breath_ax.scatter([0], [0], s=50, zorder=3, color='#4a90e2')
    if _preview_x:
        px = np.array(_preview_x)
        py = np.array(_preview_y)
        mask = (px >= now_anim - window - 1) & (px <= now_anim + window + 1)
        visible_x = px[mask]
        visible_y = py[mask]
        rel_x = visible_x - now_anim
        _curve_past.set_data(rel_x, visible_y)
    y_now = calculate_breath_y((now_anim - _row_start_time) % max(1e-6, T_active), a,b,c,d)
    _ball_dot.set_offsets(np.array([[0, y_now]]))
    breath_ax.set_xlim(-window, window)
    breath_canvas.draw_idle()
    root.after(40, update_breath_plot)

# --------------------------- Main Shutdown ---------------------------

def on_closing():
    global _running
    if not _running: return
    _running = False
    try: ui_info("Afsluiten...") 
    except: pass
    async def graceful_exit():
        global ingest_client
        if ingest_client:
            try: await ingest_client.__aexit__(None, None, None)
            except: pass
        global polar_device
        if polar_device:
            try:
                await polar_device.disconnect()
            except: pass
        loop.stop()
        root.after(0, root.destroy)
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(graceful_exit(), loop)
    else:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
loop = asyncio.new_event_loop()
threading.Thread(target=lambda: loop.run_forever(), daemon=True).start()

loop.create_task(breath_keepalive())

apply_dark_theme(root, listbox, text_box, alerts_text, [fig, breath_fig], [ax, ax2, breath_ax, ax2_breath])
update_button_states()
root.after(500, scan_clicked)
root.after(200, update_plot)

if __name__ == "__main__":
    root.mainloop()