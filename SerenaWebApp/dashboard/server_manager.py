# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import threading
import time
from sensor_config import get_server_dir

class ServerManager:
    def __init__(self, log_callback):
        self.process = None
        self.log_callback = log_callback # Functie om tekst naar de GUI te sturen

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, version=None):
        if self.is_running():
            self.log_callback("[info] Server draait al.")
            return False

        server_dir = get_server_dir()
        if not os.path.isdir(server_dir):
            self.log_callback(f"[fout] Server-map niet gevonden: {server_dir}")
            return False

        env = os.environ.copy()
        if version:
            env["RESP_RR_VERSION"] = version
            self.log_callback(f"[actie] Start server met RESP_RR_VERSION={version}...")
        else:
            self.log_callback("[actie] Start server (default)...")

        cmd = [
            sys.executable, "-m", "uvicorn", "server.main:app",
            "--host", "0.0.0.0", "--port", "8000", "--workers", "1"
        ]
        
        # Windows specifieke flag om geen extra venster te openen
        create_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        try:
            self.process = subprocess.Popen(
                cmd, cwd=server_dir, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=create_flags
            )
            # Start thread om output te lezen
            threading.Thread(target=self._read_output, daemon=True).start()
            time.sleep(1.5) # Even wachten tot hij echt up is
            return True
        except Exception as e:
            self.log_callback(f"[fout] Kon server niet starten: {e}")
            return False

    def stop(self):
        if self.is_running():
            self.log_callback("[actie] Server stoppen...")
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.log_callback("[info] Server gestopt.")
            except Exception as e:
                self.log_callback(f"[fout] Stop mislukt: {e}")
        else:
            self.log_callback("[info] Geen draaiende server.")
        
        self.process = None

    def _read_output(self):
        """Leest stdout van het server proces en stuurt het naar de GUI."""
        if self.process and self.process.stdout:
            for line in self.process.stdout:
                self.log_callback(line.strip())