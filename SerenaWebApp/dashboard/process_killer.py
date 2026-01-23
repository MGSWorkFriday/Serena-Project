# process_killer.py
import os
import signal
import subprocess
import re

class ProcessKiller:
    def __init__(self, log_callback, port=8000):
        self.log_callback = log_callback
        self.port = port

    def _log(self, text):
        self.log_callback(f"[killer] {text}")

    def find_and_kill_process(self):
        """Zoekt de PID van het proces dat de gespecificeerde poort gebruikt en sluit het af."""
        self._log(f"Zoeken naar proces op poort {self.port}...")
        
        pid = self._get_pid_on_port()
        
        if pid:
            self._log(f"Proces gevonden op poort {self.port}. PID: {pid}")
            return self._kill_process(pid)
        else:
            self._log(f"Geen proces gevonden op poort {self.port}.")
            return False

    def _get_pid_on_port(self):
        """Haalt de PID op, afhankelijk van het besturingssysteem."""
        if os.name == 'nt':  # Windows
            return self._get_pid_on_port_windows()
        else:  # Linux/macOS
            return self._get_pid_on_port_unix()

    def _get_pid_on_port_windows(self):
        """Zoekt PID op Windows met 'netstat' en 'findstr'."""
        try:
            # Commando om TCP-verbindingen te tonen, inclusief de PID
            cmd = f'netstat -ano | findstr LISTEN | findstr :{self.port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            output = result.stdout.strip()

            if output:
                # Output ziet eruit als: TCP 0.0.0.0:8000 0.0.0.0:0 LISTENING 4567
                # Het laatste getal is de PID
                lines = output.splitlines()
                # Neem de laatste kolom van de laatste relevante regel
                pid_str = lines[-1].split()[-1] 
                return int(pid_str)
            return None
        except Exception as e:
            self._log(f"Fout bij zoeken PID (Windows): {e}")
            return None

    def _get_pid_on_port_unix(self):
        """Zoekt PID op Linux/macOS met 'lsof' of 'fuser'."""
        try:
            # Gebruik 'lsof' (list open files)
            cmd = f'lsof -t -i :{self.port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            
            if output:
                # De output is puur de PID
                return int(output.splitlines()[0])
            return None
        except subprocess.CalledProcessError as e:
            # lsof geeft een non-zero exit code als er niets gevonden wordt. Dat is OK.
            if "no process found" not in e.stderr:
                 self._log(f"Fout bij zoeken PID (Unix): {e.stderr.strip()}")
            return None
        except Exception as e:
            self._log(f"Onverwachte fout bij zoeken PID (Unix): {e}")
            return None

    def _kill_process(self, pid):
        """Sluit het proces af, afhankelijk van het besturingssysteem."""
        try:
            if os.name == 'nt':  # Windows
                # Gebruik 'taskkill' voor Windows
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True, capture_output=True, text=True)
                self._log(f"Succesvol proces {pid} afgesloten met taskkill.")
            else:  # Linux/macOS
                # Gebruik signal.SIGKILL voor Unix
                os.kill(pid, signal.SIGKILL)
                self._log(f"Succesvol proces {pid} afgesloten met SIGKILL.")
            return True
        except Exception as e:
            self._log(f"Fout bij afsluiten proces {pid}: {e}")
            return False

if __name__ == '__main__':
    # Voorbeeld test
    def print_log(msg):
        print(msg)
        
    manager = ProcessKiller(print_log, port=8000)
    manager.find_and_kill_process()