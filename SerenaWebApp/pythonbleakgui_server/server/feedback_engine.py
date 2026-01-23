# server/feedback_engine.py
import json
import random
import time
from pathlib import Path
from typing import Dict, Any, Tuple

RULES_FILE = Path(__file__).parent / "feedback_rules.json"

class FeedbackEngine:
    def __init__(self):
        # Default waarden (fallback als ze niet in de JSON staan)
        self.DEFAULT_STABILITY = 3.0
        self.DEFAULT_REPEAT = 12.0
        self.DEFAULT_VISUAL = 2.0

        self.STABILITY_DURATION = self.DEFAULT_STABILITY
        self.REPEAT_INTERVAL = self.DEFAULT_REPEAT
        self.VISUAL_INTERVAL = self.DEFAULT_VISUAL

        self.rules = {}
        self.load_rules()
        
        # State tracking
        self.last_target_rr = None
        self.target_change_ts = 0.0
        
        # Audio State
        self.last_spoken_category = "" 
        self.last_spoken_ts = 0.0
        
        # STABILITEIT TRACKING (Debounce)
        self.pending_category = ""     # De categorie die we nu zien
        self.pending_ts = 0.0          # Wanneer deze categorie begon
        
        # Timers & Instellingen
        self.last_visual_ts = 0.0
        
        # Cache
        self.cached_text = "Wachten..."
        self.cached_color = ""

    def _apply_settings(self, rules_data: Dict[str, Any]):
        """Interne helper om instellingen uit de JSON te laden."""
        settings = rules_data.get("settings", {})
        
        # Haal waardes op of gebruik defaults
        self.STABILITY_DURATION = float(settings.get("stability_duration", self.DEFAULT_STABILITY))
        self.REPEAT_INTERVAL = float(settings.get("repeat_interval", self.DEFAULT_REPEAT))
        self.VISUAL_INTERVAL = float(settings.get("visual_interval", self.DEFAULT_VISUAL))
        
        # Debug print (optioneel, handig om te zien of het werkt in je console)
        # print(f"[FEEDBACK] Settings geladen: Stab={self.STABILITY_DURATION}s, "
        #       f"Rep={self.REPEAT_INTERVAL}s, Vis={self.VISUAL_INTERVAL}s")

    def load_rules(self):
        if not RULES_FILE.exists():
            self.rules = {} 
        else:
            try:
                with open(RULES_FILE, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
                
                # Pas de instellingen direct toe na het laden
                self._apply_settings(self.rules)
                    
            except Exception as e:
                print(f"[FEEDBACK] Fout bij laden regels: {e}")

    def save_rules(self, new_rules: Dict[str, Any]):
        try:
            with open(RULES_FILE, "w", encoding="utf-8") as f:
                json.dump(new_rules, f, indent=2)
            
            self.rules = new_rules
            # Update de timers direct in het geheugen
            self._apply_settings(new_rules)
            
            return True
        except Exception as e:
            print(f"[FEEDBACK] Kon niet opslaan: {e}")
            return False

    def get_feedback(self, target_rr: float, actual_rr: float) -> Tuple[str, str, str]:
        """
        Returns: (visual_text, audio_text, color_code)
        """
        if not target_rr or target_rr <= 0 or not actual_rr or actual_rr <= 0:
            return "Wachten...", "", ""

        now = time.time()

        # 1. Reset bij nieuwe sessie
        if target_rr != self.last_target_rr:
            self.last_target_rr = target_rr
            self.target_change_ts = now
            self.last_spoken_category = "" 
            self.pending_category = ""
            self.pending_ts = now
            
        # 2. Bepaal Huidige 'Ruwe' Categorie (Instant)
        blue_limit = self.rules.get("blue", {}).get("threshold_sec", 22)
        elapsed = now - self.target_change_ts
        
        current_raw_category = ""
        current_color = ""

        if elapsed < blue_limit:
            current_raw_category = "blue"
            current_color = "accent"
        else:
            diff = actual_rr - target_rr
            pct = (abs(diff) / target_rr) * 100.0
            
            green_lim = self.rules.get("green", {}).get("threshold_pct", 5)
            orange_lim = self.rules.get("orange", {}).get("threshold_pct", 15)

            if pct <= green_lim:
                current_raw_category = "green"
                current_color = "ok"
            elif pct <= orange_lim:
                current_raw_category = "orange"
                current_color = "warn"
            else:
                current_color = "bad"
                current_raw_category = "red_fast" if diff > 0 else "red_slow"

        # ---------------------------------------------------------
        # 3. STABILITEIT & AUDIO LOGICA
        # ---------------------------------------------------------
        
        # A. Is de categorie veranderd t.o.v. vorig frame?
        if current_raw_category != self.pending_category:
            # RESET TIMER: De status is net gewijzigd (of glitch)
            self.pending_category = current_raw_category
            self.pending_ts = now 
            
        # B. Hoe lang is deze categorie nu al stabiel?
        stability_time = now - self.pending_ts
        
        # GEBRUIK HIER DE DYNAMISCHE VARIABELE:
        is_stable = stability_time >= self.STABILITY_DURATION

        should_speak = False
        
        # We spreken ALLEEN als de huidige categorie > X seconden stabiel is
        if is_stable:
            # Spreek als de stabiele categorie anders is dan wat we laatst zeiden
            if self.pending_category != self.last_spoken_category:
                should_speak = True
            # Of als herinnering (time-out) -> GEBRUIK DYNAMISCHE VARIABELE
            elif (now - self.last_spoken_ts) > self.REPEAT_INTERVAL:
                should_speak = True
        
        # ---------------------------------------------------------
        # 4. SAMENSTELLING BERICHTEN
        # ---------------------------------------------------------
        audio_text = ""      # Standaard leeg (stilte)
        visual_text = self.cached_text

        if should_speak:
            # We pakken een bericht dat hoort bij de STABIELE categorie
            msg_obj = self._pick_message(self.pending_category)
            if msg_obj:
                # Update tekst voor scherm
                visual_text = msg_obj.get("text", "")
                # Update audio (alleen nu!)
                audio_text = msg_obj.get("audio_text", visual_text)
                
                # State bijwerken
                self.last_spoken_ts = now
                self.last_visual_ts = now
                self.last_spoken_category = self.pending_category
                self.cached_text = visual_text

        # GEBRUIK HIER DE DYNAMISCHE VARIABELE:
        elif (now - self.last_visual_ts) > self.VISUAL_INTERVAL:
             # Visuele updates mogen vaker, gebaseerd op de RUWE status
             msg_obj = self._pick_message(current_raw_category)
             if msg_obj:
                 visual_text = msg_obj.get("text", "")
                 self.last_visual_ts = now
                 self.cached_text = visual_text

        self.cached_color = current_color
        
        return visual_text, audio_text, current_color

    def _pick_message(self, category: str) -> dict:
        cat_data = self.rules.get(category)
        if not cat_data or "messages" not in cat_data or not cat_data["messages"]:
            return {}
        msgs = cat_data["messages"]
        weights = [m.get("weight", 1) for m in msgs]
        if not msgs: return {}
        return random.choices(msgs, weights=weights, k=1)[0]

engine = FeedbackEngine()