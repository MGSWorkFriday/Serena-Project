# -*- coding: utf-8 -*-
"""Feedback generator service"""
from __future__ import annotations

import logging
import random
import time
from typing import Dict, Any, Tuple, Optional

from app.database import get_database
from app.schemas.feedback_rules import FeedbackRules

logger = logging.getLogger(__name__)


class FeedbackGenerator:
    """Generates feedback based on target vs actual respiratory rate"""
    
    def __init__(self):
        self._rules_cache: Optional[Dict[str, Any]] = None
        self._cache_ts = 0.0
        self._cache_ttl = 60.0  # Cache for 60 seconds
        
        # State tracking per session
        self._session_state: Dict[str, Dict[str, Any]] = {}
    
    async def _load_rules(self) -> Dict[str, Any]:
        """Load feedback rules from database (with caching)"""
        now = time.time()
        
        if self._rules_cache and (now - self._cache_ts) < self._cache_ttl:
            return self._rules_cache
        
        try:
            db = await get_database()
            rules_doc = await db.feedback_rules.find_one({})
            
            if rules_doc:
                feedback_rules = FeedbackRules.from_dict(rules_doc)
                self._rules_cache = feedback_rules.rules
                self._cache_ts = now
                return self._rules_cache
        except Exception as e:
            logger.error(f"Error loading feedback rules: {e}")
        
        # Return default rules
        feedback_rules = FeedbackRules()
        self._rules_cache = feedback_rules.rules
        self._cache_ts = now
        return self._rules_cache
    
    def _get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get or create session state"""
        if session_id not in self._session_state:
            self._session_state[session_id] = {
                "last_target_rr": None,
                "target_change_ts": 0.0,
                "last_spoken_category": "",
                "pending_category": "",
                "pending_ts": 0.0,
                "last_visual_ts": 0.0,
                "last_spoken_ts": 0.0,
                "cached_text": "Wachten...",
                "cached_color": "",
            }
        return self._session_state[session_id]
    
    async def get_feedback(self, session_id: str, target_rr: float, actual_rr: float) -> Tuple[str, str, str]:
        """
        Returns: (visual_text, audio_text, color_code)
        """
        if not target_rr or target_rr <= 0 or not actual_rr or actual_rr <= 0:
            return "Wachten...", "", ""
        
        rules = await self._load_rules()
        state = self._get_session_state(session_id)
        now = time.time()
        
        # Reset bij nieuwe sessie
        if target_rr != state["last_target_rr"]:
            state["last_target_rr"] = target_rr
            state["target_change_ts"] = now
            state["last_spoken_category"] = ""
            state["pending_category"] = ""
            state["pending_ts"] = now
        
        # Bepaal huidige categorie
        blue_limit = rules.get("blue", {}).get("threshold_sec", 30.0)
        elapsed = now - state["target_change_ts"]
        
        current_raw_category = ""
        current_color = ""
        
        if elapsed < blue_limit:
            current_raw_category = "blue"
            current_color = "accent"
        else:
            diff = actual_rr - target_rr
            pct = (abs(diff) / target_rr) * 100.0
            
            green_lim = rules.get("green", {}).get("threshold_pct", 5)
            orange_lim = rules.get("orange", {}).get("threshold_pct", 15)
            
            if pct <= green_lim:
                current_raw_category = "green"
                current_color = "ok"
            elif pct <= orange_lim:
                current_raw_category = "orange"
                current_color = "warn"
            else:
                current_color = "bad"
                current_raw_category = "red_fast" if diff > 0 else "red_slow"
        
        # Stabiliteit & Audio logica
        if current_raw_category != state["pending_category"]:
            state["pending_category"] = current_raw_category
            state["pending_ts"] = now
        
        stability_time = now - state["pending_ts"]
        settings = rules.get("settings", {})
        stability_duration = settings.get("stability_duration", 3.0)
        repeat_interval = settings.get("repeat_interval", 7.0)
        visual_interval = settings.get("visual_interval", 7.0)
        
        is_stable = stability_time >= stability_duration
        should_speak = False
        
        if is_stable:
            if state["pending_category"] != state["last_spoken_category"]:
                should_speak = True
            elif (now - state["last_spoken_ts"]) > repeat_interval:
                should_speak = True
        
        audio_text = ""
        visual_text = state["cached_text"]
        
        if should_speak:
            msg_obj = self._pick_message(rules, state["pending_category"])
            if msg_obj:
                visual_text = msg_obj.get("text", "")
                audio_text = msg_obj.get("audio_text", visual_text)
                state["last_spoken_ts"] = now
                state["last_visual_ts"] = now
                state["last_spoken_category"] = state["pending_category"]
                state["cached_text"] = visual_text
        elif (now - state["last_visual_ts"]) > visual_interval:
            msg_obj = self._pick_message(rules, current_raw_category)
            if msg_obj:
                visual_text = msg_obj.get("text", "")
                state["last_visual_ts"] = now
                state["cached_text"] = visual_text
        
        state["cached_color"] = current_color
        
        return visual_text, audio_text, current_color
    
    def _pick_message(self, rules: Dict[str, Any], category: str) -> dict:
        """Pick a random message from category based on weights"""
        cat_data = rules.get(category)
        if not cat_data or "messages" not in cat_data or not cat_data["messages"]:
            return {}
        msgs = cat_data["messages"]
        weights = [m.get("weight", 1) for m in msgs]
        if not msgs: return {}
        return random.choices(msgs, weights=weights, k=1)[0]
    
    def clear_session_state(self, session_id: str):
        """Clear state for a session"""
        if session_id in self._session_state:
            del self._session_state[session_id]


# Global feedback generator instance
feedback_generator = FeedbackGenerator()
