# server/techniques_engine.py
import json
import os
from pathlib import Path
from typing import Dict, Any

DATA_FILE = Path(__file__).parent / "techniques.json"

class TechniquesEngine:
    def __init__(self):
        self.techniques = {}
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not DATA_FILE.exists():
            try:
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            except Exception as e:
                print(f"[TECHNIQUES] Kon initieel bestand niet maken: {e}")

    def load(self):
        if not DATA_FILE.exists():
            self.techniques = {}
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.techniques = json.load(f)
        except Exception as e:
            print(f"[TECHNIQUES] Fout bij laden: {e}")
            self.techniques = {}

    def get_all(self):
        self.load()
        return self.techniques

    # AANGEPAST: Extra argument show_in_app
    def save_technique(self, name: str, description: str, protocol_data: list, param_version: str = "Default", show_in_app: bool = False):
        self.load()
        
        self.techniques[name] = {
            "description": description,
            "param_version": param_version,
            "show_in_app": show_in_app, # NIEUW: Opslaan
            "protocol": protocol_data
        }
        return self._persist()

    def delete_technique(self, name: str):
        self.load()
        if name in self.techniques:
            del self.techniques[name]
            return self._persist()
        return False

    def _persist(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.techniques, f, indent=2)
            return True
        except Exception as e:
            print(f"[TECHNIQUES] Fout bij schrijven: {e}")
            return False

engine = TechniquesEngine()