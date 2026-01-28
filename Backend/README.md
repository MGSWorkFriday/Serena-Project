# Serena Backend

FastAPI backend met MongoDB voor de Serena ademhalingsoefening applicatie.

## Setup

### Vereisten
- Docker en Docker Compose
- Python 3.10+ (voor lokale development)

### MongoDB Starten

```bash
# Start MongoDB container
docker-compose up -d mongodb

# Optioneel: Start MongoDB Express (database management UI)
docker-compose --profile tools up -d mongo-express
# Toegankelijk op http://localhost:8081
```

### Environment Variabelen

Kopieer `.env.example` naar `.env` en pas aan:

```bash
cp .env.example .env
```

### Database Connectie

De MongoDB connection string format:
```
mongodb://[username]:[password]@[host]:[port]/[database]?authSource=admin
```

Voorbeeld:
```
mongodb://admin:changeme@localhost:27017/serena?authSource=admin
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

De API is dan beschikbaar op:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/healthz

## API Endpoints

### Health & Status
- `GET /healthz` - Health check
- `GET /api/v1/status` - Detailed system status

### Devices
- `GET /api/v1/devices` - List all devices
- `GET /api/v1/devices/{device_id}` - Get device
- `POST /api/v1/devices` - Create device
- `PATCH /api/v1/devices/{device_id}` - Update device
- `GET /api/v1/devices/{device_id}/sessions` - Get device sessions

### Sessions
- `GET /api/v1/sessions` - List sessions (with filters)
- `GET /api/v1/sessions/{session_id}` - Get session
- `POST /api/v1/sessions` - Start session
- `PATCH /api/v1/sessions/{session_id}` - Update session
- `POST /api/v1/sessions/{session_id}/end` - End session

### Signals
- `GET /api/v1/signals` - Query signals (with filters)
- `GET /api/v1/signals/recent` - Get recent signals
- `GET /api/v1/signals/{signal_id}` - Get signal by ID
- `POST /api/v1/ingest` - Ingest sensor data (NDJSON or JSON)
- `GET /api/v1/stream` - SSE stream for real-time data

### Techniques
- `GET /api/v1/techniques` - List all techniques
- `GET /api/v1/techniques/public` - List public techniques
- `GET /api/v1/techniques/{name}` - Get technique
- `POST /api/v1/techniques` - Create/update technique
- `DELETE /api/v1/techniques/{name}` - Delete technique

### Feedback
- `GET /api/v1/feedback/rules` - Get feedback rules
- `POST /api/v1/feedback/rules` - Update feedback rules
- `GET /api/v1/feedback/rules/settings` - Get feedback settings

### Parameter Sets
- `GET /api/v1/param_versions` - List parameter versions
- `GET /api/v1/param_versions/{version}` - Get parameter set
- `POST /api/v1/param_versions` - Create parameter set
- `PATCH /api/v1/param_versions/{version}` - Update parameter set

## Database Modellen

Zie `app/schemas/` voor MongoDB document schemas:
- Device
- Session
- SignalRecord
- Technique
- FeedbackRules
- ParameterSet

## Data Migratie

Zie `scripts/README.md` voor instructies om bestaande JSONL logs te migreren naar MongoDB.

## Project Structuur

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # MongoDB connection
│   ├── models/              # Pydantic models (request/response)
│   ├── schemas/             # MongoDB document schemas
│   ├── api/
│   │   └── v1/              # API v1 endpoints
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── scripts/                  # Migration scripts
├── docker-compose.yml
├── requirements.txt
└── .env
```
