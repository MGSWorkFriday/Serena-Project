# config.py
import os

# --- Signaal Instellingen ---
SAMPLE_RATE = 130          # Polar H10 ECG ~130 Hz
WINDOW_SECONDS = 120       # ringbufferlengte voor de grafiek
DISPLAY_SECONDS = 10       # hoeveelheid die we rechts in beeld schuiven

# --- Bestanden en Mappen ---
# Let op: dubbele backslashes voor Windows paden
PROTOCOL_DIR = "C:\\Serena\\NaamBestanden"
INDEX_FILE = os.path.join(PROTOCOL_DIR, "protocol_index.jsonl")

# --- Ingest (Server) Defaults ---
DEFAULT_INGEST_URL = "http://127.0.0.1:8000/ingest"
DEFAULT_BATCH_MS = 250
DEFAULT_BATCH_SIZE = 200