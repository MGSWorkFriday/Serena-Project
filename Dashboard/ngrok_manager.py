# ngrok_manager.py
import subprocess
import threading
import time
import os
import signal
import requests 
import socket # <--- Nodig om computernaam te lezen

class NgrokManager:
    def __init__(self, log_callback, port=8000):
        self.log_callback = log_callback
        self.port = port
        self.ngrok_process = None
        self.public_url = None
        self.stop_event = threading.Event()
        self.api_url = "http://127.0.0.1:4040/api/tunnels" 
        
        # JOUW CONFIGURATIE
        #self.static_domain = "superrational-blocky-tynisha.ngrok-free.dev" PETER
        self.static_domain = "unfazedly-mirier-justus.ngrok-free.dev"
        
        # VUL HIER JOUW COMPUTERNAAM IN (die je net hebt opgezocht)
        #self.my_computer_name = "MSI"  PETER
        self.my_computer_name = "GMP"

    def _log(self, text):
        self.log_callback(f"[ngrok] {text}")

    def get_public_url(self):
        return self.public_url

    def start(self):
        if self.is_running():
            self._log("Ngrok draait al.")
            return

        self.public_url = None
        self.stop_event.clear()
        
        cmd = ["ngrok", "http"]
        
        # --- DE SLIMME CHECK ---
        current_host = socket.gethostname()
        
        # We gebruiken het vaste domein ALLEEN als de hostnaam klopt
        if self.static_domain and current_host == self.my_computer_name:
            self._log(f"Herken PC '{current_host}': Start met vast domein {self.static_domain}...")
            cmd.append(f"--domain={self.static_domain}")
        else:
            self._log(f"PC '{current_host}' is niet de eigenaar. Start met random domein...")
            
        cmd.append(str(self.port))
        
        try:
            # --- START CORRECTIE VOOR SILENT MODE ---
            flags = 0
            if os.name == 'nt': 
                flags = subprocess.CREATE_NO_WINDOW
            
            self.ngrok_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags
            )
            # --- EINDE CORRECTIE VOOR SILENT MODE ---

            threading.Thread(target=self._poll_for_url, daemon=True).start()
            
        except FileNotFoundError:
            self._log("Fout: 'ngrok' commando niet gevonden.")
        except Exception as e:
            self._log(f"Onverwachte fout bij starten ngrok: {e}")

    def _poll_for_url(self):
        for _ in range(30): 
            if self.stop_event.is_set(): return
            try:
                response = requests.get(self.api_url)
                response.raise_for_status()
                data = response.json()
                for tunnel in data.get('tunnels', []):
                    if tunnel['proto'] == 'https':
                        self.public_url = tunnel['public_url']
                        
                        # Extra check: Waarschuw als het toch mis ging
                        if self.static_domain and socket.gethostname() == self.my_computer_name:
                            if self.static_domain not in self.public_url:
                                self._log(f"LET OP: Vast domein mislukt. Gekregen: {self.public_url}")
                        
                        self.log_callback(f"URL_FOUND:{self.public_url}") 
                        return
            except requests.exceptions.RequestException:
                pass 
            time.sleep(1)

        if not self.public_url:
            self._log("Kon URL niet ophalen. Check ngrok.")

    def stop(self):
        if self.ngrok_process and self.ngrok_process.poll() is None:
            self._log("Stop ngrok...")
            self.stop_event.set()
            try:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
            except Exception:
                self.ngrok_process.kill()
            self.ngrok_process = None
            self.public_url = None
            self._log("Ngrok gestopt.")
            return True
        return False

    def is_running(self):
        return self.ngrok_process is not None and self.ngrok_process.poll() is None

if __name__ == '__main__':
    def print_log(msg): print(msg)
    manager = NgrokManager(print_log)
    manager.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
