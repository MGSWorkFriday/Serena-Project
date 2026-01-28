# Serena Backend - Server Starten

## Vereisten

1. **Python 3.11 of 3.12** (Python 3.13 heeft compatibiliteitsproblemen met motor/pymongo)
2. **Docker** (voor MongoDB)
3. **Dependencies geïnstalleerd**

## Setup Stappen

### 1. Python Environment
```bash
# Gebruik Python 3.11 of 3.12
python3.11 -m venv venv
# Of op Windows:
python -m venv venv

# Activeer virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
cd Backend
pip install -r requirements.txt
```

### 3. Environment Configuratie
```bash
# .env bestand wordt automatisch gebruikt
# Standaard waarden zijn al ingesteld in config.py
```

### 4. Start MongoDB
```bash
docker-compose up -d mongodb
```

### 5. Start Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test Endpoints

- **Health Check**: http://localhost:8000/healthz
- **API Docs**: http://localhost:8000/docs
- **Status**: http://localhost:8000/api/v1/status

## API Endpoints Overzicht

### Health & Status
- `GET /healthz` - Quick health check
- `GET /api/v1/ping` - Licht contactmoment (geen DB); gebruikt door de app voor "Offline"-detectie
- `GET /api/v1/status` - Detailed status (inclusief database)

### Devices
- `GET /api/v1/devices` - List devices
- `GET /api/v1/devices/{device_id}` - Get device
- `POST /api/v1/devices` - Create device
- `PATCH /api/v1/devices/{device_id}` - Update device
- `GET /api/v1/devices/{device_id}/sessions` - Device sessions

### Sessions
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{session_id}` - Get session
- `POST /api/v1/sessions` - Start session
- `PATCH /api/v1/sessions/{session_id}` - Update session
- `POST /api/v1/sessions/{session_id}/end` - End session

### Signals
- `GET /api/v1/signals` - Query signals
- `GET /api/v1/signals/recent` - Recent signals
- `GET /api/v1/signals/{signal_id}` - Get signal
- `POST /api/v1/ingest` - Ingest data
- `GET /api/v1/stream` - SSE stream

### Techniques
- `GET /api/v1/techniques` - All techniques
- `GET /api/v1/techniques/public` - Public techniques
- `GET /api/v1/techniques/{name}` - Get technique
- `POST /api/v1/techniques` - Create/update
- `DELETE /api/v1/techniques/{name}` - Delete

### Feedback
- `GET /api/v1/feedback/rules` - Get rules
- `POST /api/v1/feedback/rules` - Update rules
- `GET /api/v1/feedback/rules/settings` - Get settings

### Parameter Sets
- `GET /api/v1/param_versions` - List versions
- `GET /api/v1/param_versions/{version}` - Get set
- `POST /api/v1/param_versions` - Create set
- `PATCH /api/v1/param_versions/{version}` - Update set

## Troubleshooting

### Motor/PyMongo niet geïnstalleerd
- **Probleem**: Python 3.13 is te nieuw
- **Oplossing**: Gebruik Python 3.11 of 3.12

### `"database": "error"` in /api/v1/status
De Backend kan dan niet met MongoDB praten. Oplossingen:

1. **MongoDB draait niet**
   - `docker ps` (of `docker ps | findstr mongo`) – container `serena-mongodb` moet *Up* zijn.
   - Start: `docker-compose up -d` (of `docker-compose up -d mongodb`).

2. **Backend opnieuw starten**
   - Stop uvicorn (Ctrl+C) en start opnieuw: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
   - De Backend maakt bij opstart opnieuw verbinding met MongoDB.

3. **Inloggegevens en host**
   - Standaard: `admin` / `changeme`, host `localhost`, poort `27017`.
   - In `Backend/.env`: `MONGO_ROOT_USERNAME`, `MONGO_ROOT_PASSWORD`, `MONGO_HOST`, `MONGO_PORT` moeten overeenkomen met de MongoDB-container (o.a. `MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD` in `docker-compose`).

4. **Concrete fout zien**
   - Zet in `.env`: `APP_DEBUG=true`.
   - Open opnieuw `http://localhost:8000/api/v1/status`. Bij `"database": "error"` staat er nu ook `"database_error": "..."` (bijv. "Connection refused" of "Authentication failed").

### MongoDB container / connectie testen
- **Container draait?**: `docker ps | findstr mongodb`
- **Start**: `docker-compose up -d mongodb`
- **Ping vanuit container**: `docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"`

### Import errors
- **Check**: Zijn alle dependencies geïnstalleerd?
  ```bash
  pip list | findstr -i "fastapi motor pymongo numpy scipy"
  ```

## Development Mode

```bash
# Met auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Met logging
uvicorn app.main:app --reload --log-level debug
```
