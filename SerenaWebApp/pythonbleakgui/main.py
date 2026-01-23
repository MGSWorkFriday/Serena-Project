# main.py
# -*- coding: utf-8 -*-
"""
Wearable ECG — Polar H10 (Windows)
Modular Refactor - Performance Fix & Pre-draw Graph + Tabel Usability Fixes
** Aangepast: Auto-scan bij opstarten & Nette disconnect bij afsluiten (X) **
"""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import time
import csv
import os
import sys 
import collections
import traceback
import numpy as np
import json
from datetime import datetime

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

# ----------------------------- Globals --------------------------------

loop = None                
polar_device = None        
streaming = False          

# Buffers & Detector
ecg_buffer = collections.deque(maxlen=config.SAMPLE_RATE * config.WINDOW_SECONDS)
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
        except: pass # Negeer fouten als venster al dicht is
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
    
    # We proberen de disconnect te triggeren, maar wachten er niet te lang op bij restart
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

# -------------------- Polar callbacks (DATA) --------------------------

def on_data(data):
    global csv_writer, save_file, ecg_field_name, ingest_client
    global recording_active, recording_file
    # Globals nodig voor TargetRR berekening
    global breathing_active, _active_protocol_data, _current_row_idx 

    if isinstance(data, ECGData):
        # 1. Veldnaam bepalen (indien nog niet bekend)
        if ecg_field_name is None:
            for fld in ["data", "microvolts", "samples_uv", "samples", "values", "uV"]:
                if hasattr(data, fld):
                    ecg_field_name = fld
                    ui_info(f"[ECG] samples veld: {ecg_field_name}")
                    break
            if ecg_field_name is None:
                ui_warn("[ECG] onbekend sample-veld")
                return

        # 2. Samples uitlezen
        try:
            samples_raw = getattr(data, ecg_field_name)
        except Exception as e:
            ui_warn(f"[ECG] kon samples niet lezen: {e}")
            return

        # Samples normaliseren naar lijst
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

        # Buffer en UI update
        ecg_buffer.extend(samples)
        ui_set_text(" ".join(str(v) for v in samples))

        # 3. Timestamp bepalen
        ts_any = getattr(data, "timestamp", None)
        if isinstance(ts_any, (int, float)) and ts_any > 1e12:
            ts_ms = int(ts_any / 1_000_000) 
        elif isinstance(ts_any, (int, float)):
            ts_ms = int(ts_any)             
        else:
            ts_ms = int(time.time() * 1000)

        # 4. TargetRR Berekenen (NU HIER BOVENAAN)
        target_rr = None
        if breathing_active and _active_protocol_data:
            try:
                # We pakken de data van de rij die nu geanimeerd wordt
                if 0 <= _current_row_idx < len(_active_protocol_data):
                    p = _active_protocol_data[_current_row_idx]
                    # Totaal aantal seconden per cyclus = In + Hold1 + Uit + Hold2
                    cycle_duration = p[0] + p[1] + p[2] + p[3]
                    
                    if cycle_duration > 0:
                        target_rr = round(60.0 / cycle_duration, 2)
            except Exception:
                pass 

        # 5. Record opbouwen in specifieke volgorde
        #    Volgorde: signal -> ts -> TargetRR (optioneel) -> samples
        
        # Stap A: Metadata
        base_record = {
            "signal": "ecg", 
            "ts": ts_ms
        }
        
        # Stap B: TargetRR invoegen (indien aanwezig) direct na ts
        if target_rr is not None:
            base_record["TargetRR"] = target_rr
            
        # Stap C: Data toevoegen (samples achteraan ivm leesbaarheid)
        base_record["samples"] = samples

        # 6. CSV Logging (Legacy format, blijft ongewijzigd)
        if csv_writer:
            for s in samples:
                csv_writer.writerow([ts_ms, s])
            save_file.flush()
            
        # 7. Frontend Recording (JSONL)
        # We gebruiken hier een kopie van base_record zodat we zeker weten dat het de juiste structuur is
        if recording_active and recording_file is not None:
            try:
                loop.call_soon_threadsafe(
                    lambda: (recording_file.write(json.dumps(base_record) + '\n'), recording_file.flush()) 
                    if recording_file else None
                )
            except Exception as e:
                ui_error(f"[FE-LOG] Fout bij wegschrijven: {e}")
                
        # 8. Ingest Server
        if ingest_client is not None:
            # We sturen hetzelfde object door
            loop.call_soon_threadsafe(asyncio.create_task, ingest_client.add(base_record))

        # 9. HR Detector update
        _hrdet.add_batch(ts_ms, samples)

# --------------------------- Async taken ------------------------------

async def scan_devices():
    """Zoekt alleen naar devices met 'Polar' in de naam."""
    global found_devices
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

async def do_connect():
    """
    Connect met BLE, wacht even, en start dan de ECG stream.
    """
    global polar_device, selected_device, streaming
    if not selected_device:
        ui_warn("Selecteer een sensor")
        return
    try:
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
    """
    Stopt Ingest, en verbreekt dan de Polar verbinding.
    """
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
    """Start Ingest (Server)."""
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
    """Stop Ingest (Server)."""
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
    global recording_active, recording_file
    if recording_active:
        ui_warn("Opname loopt al.")
        return
    if not breathing_active:
        ui_warn("Start eerst de ademhalingsanimatie.")
        return

    try:
        os.makedirs(config.PROTOCOL_DIR, exist_ok=True)
        for filename in os.listdir(config.PROTOCOL_DIR):
            if filename.startswith("ECG_RAW_"):
                filepath = os.path.join(config.PROTOCOL_DIR, filename)
                try:
                    if os.path.isfile(filepath): os.remove(filepath)
                except Exception as e:
                    ui_error(f"Fout verwijderen {filename}: {e}")
        
        now = datetime.now()
        filename = f"ECG_RAW_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"
        filepath = os.path.join(config.PROTOCOL_DIR, filename)
        
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
    global _active_protocol_data
    name = name_entry.get().strip() or "OnbekendeNaam"
    try:
        os.makedirs(config.PROTOCOL_DIR, exist_ok=True)
        current_index = get_next_index()
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
        raw_files = [
            os.path.join(config.PROTOCOL_DIR, f) for f in os.listdir(config.PROTOCOL_DIR)
            if f.startswith("ECG_RAW_")
        ]
        if raw_files:
            raw_files.sort(key=os.path.getmtime)
            latest_raw_path = raw_files[-1]
            new_raw_filename = f"{index_filename_base}.jsonl" 
            try:
                os.rename(latest_raw_path, os.path.join(config.PROTOCOL_DIR, new_raw_filename))
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
            "protocol": protocol_data
        }
        with open(config.INDEX_FILE, 'a', encoding='utf-8') as f:
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

    if os.path.exists(config.INDEX_FILE):
        try:
            records = []
            with open(config.INDEX_FILE, 'r', encoding='utf-8') as f:
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
    ui_info(f"Marker naar {url}...")
    def run_api_call():
        success, msg = manual_event_api.send_inhale_marker(url)
        root.after(0, lambda: ui_info(msg) if success else ui_error(msg))
    threading.Thread(target=run_api_call, daemon=True).start()

def clear_alerts():
    alerts_text.configure(state="normal")
    alerts_text.delete("1.0", "end")
    alerts_text.configure(state="disabled")
    status_var.set("Ready")

# --------------------------- Plotting ---------------------------------

def update_plot():
    if not _running: return
    if len(ecg_buffer) < 2:
        root.after(200, update_plot)
        return

    arr = np.array(list(ecg_buffer))
    time_total = len(arr) / config.SAMPLE_RATE
    x = np.linspace(time_total - len(arr)/config.SAMPLE_RATE, time_total, len(arr))
    x_lim = (max(0.0, x[-1] - config.DISPLAY_SECONDS), x[-1])

    ax.clear()
    ax.set_title("Live ECG", color='white')
    ax.set_xlabel("Tijd (s)", color='white')
    ax.set_ylabel("Amplitude (µV)", color='white')
    ax.plot(x, arr, color='cyan', linewidth=0.5)
    ax.set_xlim(x_lim)
    ax.grid(True, alpha=0.5, color='gray')

    if rr_display_var.get():
        rr_list = _hrdet.rr_list_ms(200)
        if len(rr_list) >= 2:
            rr_times_ms = _hrdet.peak_times_ms[-len(rr_list):]
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
    update_button_states()
    update_breath_plot()

def breath_stop():
    global _anim_running, _last_tick, breathing_active
    _anim_running = False
    _last_tick = None
    breathing_active = False
    ui_info("Adem-animatie gestopt")
    update_button_states()

def update_button_states():
    global breathing_active, recording_active
    if not all([btn_start_adem, btn_stop_adem, btn_start_recording, btn_stop_recording, btn_save_bestand]): return
    raw_exists = any(f.startswith("ECG_RAW_") for f in os.listdir(config.PROTOCOL_DIR)) if os.path.exists(config.PROTOCOL_DIR) else False
    if recording_active:
        btn_start_adem.configure(state='disabled')
        btn_stop_adem.configure(state='disabled')
    elif breathing_active:
        btn_start_adem.configure(state='disabled')
        btn_stop_adem.configure(state='enabled')
    else:
        btn_start_adem.configure(state='enabled')
        btn_stop_adem.configure(state='disabled')
    if recording_active:
        btn_start_recording.configure(state='disabled')
        btn_stop_recording.configure(state='enabled')
    else:
        btn_stop_recording.configure(state='disabled')
        btn_start_recording.configure(state='enabled' if breathing_active else 'disabled')
    btn_save_bestand.configure(state='enabled' if (not recording_active and raw_exists) else 'disabled')

# --------------------------- UI Opbouw --------------------------------

root = tk.Tk()
root.title("Wearable ECG & Breathing Coach")
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
    """Sluit de applicatie netjes af: verbreekt verbindingen en stopt de loop."""
    global _running
    
    # Voorkom dat we dit dubbel doen
    if not _running: return
    _running = False
    
    # GUI feedback (optioneel, kan zijn dat UI al deels weg is)
    try: ui_info("Afsluiten...") 
    except: pass
    
    async def graceful_exit():
        # 1. Stop Ingest
        global ingest_client
        if ingest_client:
            try: await ingest_client.__aexit__(None, None, None)
            except: pass

        # 2. Stop Polar verbinding
        global polar_device
        if polar_device:
            try:
                # We sturen de disconnect en wachten kort
                await polar_device.disconnect()
            except: pass
            
        # 3. Stop de asyncio loop
        loop.stop()
        
        # 4. Sluit het venster (terug naar main thread)
        root.after(0, root.destroy)

    # Plan de exit taak in
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(graceful_exit(), loop)
    else:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
loop = asyncio.new_event_loop()
threading.Thread(target=lambda: loop.run_forever(), daemon=True).start()
apply_dark_theme(root, listbox, text_box, alerts_text, [fig, breath_fig], [ax, ax2, breath_ax, ax2_breath])
update_button_states()
root.after(500, scan_clicked)
root.after(200, update_plot)

if __name__ == "__main__":
    root.mainloop()