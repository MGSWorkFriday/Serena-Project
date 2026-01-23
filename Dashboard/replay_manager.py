# -*- coding: utf-8 -*-
import os
import sys
import glob
import subprocess
import time
from sensor_config import get_base_dir
from sensor_api import call_rotate

class ReplayManager:
    def __init__(self, server_manager, log_callback):
        self.server = server_manager
        self.log_callback = log_callback

    def run_versions_loop(self, versions, folder, file_path, ingest_url, bulk):
        """
        Orkestreert de volledige loop:
        Voor elke versie -> Start Server -> Verwerk bestand(en) -> Stop Server.
        """
        for v in versions:
            label = v if v is not None else "<default>"
            self.log_callback(f"\n[versie-loop] ===== Versie: {label} =====")

            # 1. Start Server
            if not self.server.start(version=v):
                self.log_callback("[versie-loop] Server start gefaald, sla over.")
                continue

            try:
                # 2. Verwerk input
                if folder:
                    self._run_folder_sequence(folder, ingest_url, bulk)
                else:
                    # Single file
                    ok, msg = call_rotate(file_name=file_path)
                    self.log_callback(msg)
                    self._run_replayer_script(file_path, ingest_url, bulk)
            finally:
                # 3. Stop Server (altijd, ook bij fouten)
                self.server.stop()
                # Korte pauze om poort vrij te geven
                time.sleep(1.0) 

        self.log_callback("\n[versie-loop] Alle versies verwerkt.")

    def _run_folder_sequence(self, folder, ingest_url, bulk):
        files = sorted(glob.glob(os.path.join(folder, "*.jsonl")))
        if not files:
            self.log_callback("[info] Geen .jsonl bestanden gevonden.")
            return
        
        self.log_callback(f"[info] Start map sequence ({len(files)} bestanden)...")
        for idx, path in enumerate(files, 1):
            self.log_callback(f"\n[seq {idx}/{len(files)}] {os.path.basename(path)}")
            
            # Rotate log voordat we replayen
            ok, msg = call_rotate(file_name=path)
            self.log_callback(msg)
            
            self._run_replayer_script(path, ingest_url, bulk)

    def _run_replayer_script(self, file_path, ingest_url, bulk):
        """Roept het externe ecg_replay... script aan."""
        script_path = os.path.join(get_base_dir(), "ecg_replay_ecg_only_file_loop_monots.py")
        
        if not os.path.exists(script_path):
            self.log_callback(f"[fout] Replayer script mist: {script_path}")
            return

        cmd = [sys.executable, script_path, "--file", file_path, "--url", ingest_url, "--signals", "ecg", "--verbose"]
        if bulk:
            cmd += ["--bulk", "--format", "json"]

        try:
            # We draaien dit blokkerend (wait) omdat we in een thread zitten
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for line in proc.stdout:
                self.log_callback(line.rstrip())
            proc.wait()
        except Exception as e:
            self.log_callback(f"[fout] Replayer crash: {e}")

    def run_analyzer(self, folder_path):
        """Roept het log_analyzer.py script aan."""
        script_path = os.path.join(get_base_dir(), "log_analyzer.py")
        if not os.path.exists(script_path):
            self.log_callback("[fout] log_analyzer.py niet gevonden.")
            return

        cmd = [sys.executable, script_path, "--folder", folder_path]
        try:
            create_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=create_flags
            )
            for line in proc.stdout:
                self.log_callback(line.rstrip())
            proc.wait()
            self.log_callback("[info] Analyse klaar.")
        except Exception as e:
            self.log_callback(f"[fout] Analyse mislukt: {e}")
