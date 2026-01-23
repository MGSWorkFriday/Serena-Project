# server/main.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import json
import os
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.endpoints import healthz, ingest, recent, stream, ui, reset, rotate, rotate_get
from server.models import IngestResponse
from server import edr_extractor
from server.utils import WEB_DIR, log

# --- NIEUW: Feedback Engine Import ---
from server.feedback_engine import engine as feedback_engine
from server.techniques_engine import engine as tech_engine


# ------------ logging ------------
logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

# ------------ app ------------
app = FastAPI(title="Sensor Ingest", version="0.4")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log EDR module info
log.info("Loaded EDR module: %s", edr_extractor.__file__)
log.info("Loaded Feedback Engine with rules.")

# ------------ route registration ------------
app.get("/healthz")(healthz)
app.post("/ingest", response_model=IngestResponse)(ingest)
app.post("/reset")(reset)
app.post("/rotate")(rotate)
app.get("/rotate")(rotate_get)
app.get("/recent")(recent)
app.get("/stream")(stream)
app.get("/ui")(ui)

# ------------ Feedback Config Endpoints ------------

@app.get("/feedback/rules")
async def get_feedback_rules():
    """Geeft de huidige regels en gewichten terug aan de GUI."""
    return feedback_engine.rules

@app.post("/feedback/rules")
async def set_feedback_rules(request: Request):
    """Slaat aangepaste regels op vanuit de GUI."""
    try:
        new_rules = await request.json()
        success = feedback_engine.save_rules(new_rules)
        if not success:
            raise HTTPException(status_code=500, detail="Kon regels niet opslaan")
        return {"status": "ok", "message": "Regels opgeslagen"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ongeldige data: {e}")
        
@app.get("/techniques")
async def get_techniques():
    """Haal ALLE technieken op (voor de Admin GUI)."""
    return tech_engine.get_all()

# --- NIEUW ENDPOINT VOOR DE APP (serena.html) ---
@app.get("/techniques/public")
async def get_public_techniques():
    """Haal alleen technieken op die gemarkeerd zijn als 'Show in App'."""
    all_techs = tech_engine.get_all()
    # Filter de lijst
    public_techs = {k: v for k, v in all_techs.items() if v.get("show_in_app", False) is True}
    return public_techs
# ------------------------------------------------

@app.post("/techniques")
async def save_technique(request: Request):
    """Sla een techniek op."""
    try:
        data = await request.json()
        name = data.get("name")
        desc = data.get("description", "")
        proto = data.get("protocol", [])
        p_ver = data.get("param_version", "Default")
        
        # NIEUW: Lees de toggle uit
        show_app = data.get("show_in_app", False)
        
        if not name or not proto:
            raise HTTPException(status_code=400, detail="Naam en protocol zijn verplicht")
            
        success = tech_engine.save_technique(
            name, desc, proto, 
            param_version=p_ver, 
            show_in_app=show_app # Geef door aan engine
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Opslaan mislukt")
        return {"status": "ok", "name": name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/techniques/{name}")
async def delete_technique(name: str):
    """Verwijder een techniek."""
    success = tech_engine.delete_technique(name)
    if not success:
        raise HTTPException(status_code=404, detail="Techniek niet gevonden of verwijderen mislukt")
    return {"status": "ok", "deleted": name}


@app.get("/param_versions")
async def get_param_versions():
    """Haalt alle beschikbare 'version' strings op uit resp_rr_param_sets.json."""
    param_file = Path(__file__).resolve().parent.parent / "resp_rr_param_sets.json"
    
    if not param_file.exists():
        param_file = Path(__file__).parent / "resp_rr_param_sets.json"
    
    if not param_file.exists():
        return []

    try:
        with open(param_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            versions = [item.get("version") for item in data if "version" in item]
            return versions
        elif isinstance(data, dict):
            return list(data.keys())
            
        return []
    except Exception as e:
        log.error(f"Fout bij lezen param sets: {e}")
        return []
        
# ------------ static files ------------
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="static")