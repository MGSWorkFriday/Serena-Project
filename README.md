# Serena

Ademhalingsoefening-applicatie met real-time biofeedback via hartslagsensor.

## Projectstructuur

| Map | Technologie | Beschrijving |
|-----|-------------|--------------|
| `Backend/` | FastAPI + MongoDB | REST API, SSE streaming, sessies, techniques |
| `Mobile/` | Expo / React Native | Cross-platform app (iOS, Android, Web) |
| `Dashboard/` | Python | Sensor dashboard en monitoring |
| `SerenaWebApp/` | Python | Legacy web applicatie en server |

## Aan de slag (nieuw teamlid)

### 1. Repository clonen

```bash
git clone <repository-url>
cd Serena
```

### 2. Vereisten installeren

- **Git** – versiebeheer
- **Docker Desktop** – voor MongoDB database
- **Python 3.11 of 3.12** – voor Backend (3.13 geeft problemen met dependencies)
- **Node.js 18+** – voor Mobile app

### 3. Backend + Mobile starten

Zie **[START_APP.md](START_APP.md)** voor gedetailleerde instructies.

**Samenvatting:**

```powershell
# Terminal 1 – Backend
cd Backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d mongodb
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 – Mobile
cd Mobile
npm install
npm start
```

### 4. Controleren

- Backend API: http://localhost:8000/docs
- Health check: http://localhost:8000/healthz

## Documentatie

| Document | Inhoud |
|----------|--------|
| [START_APP.md](START_APP.md) | Complete setup-handleiding met troubleshooting |
| [Backend/README.md](Backend/README.md) | API endpoints en database modellen |
| [Backend/scripts/README.md](Backend/scripts/README.md) | Data migratie scripts |

## Development workflow

1. **Pull** – Begin elke sessie met `git pull`
2. **Branch** – Werk aan features in een aparte branch
3. **Commit** – Maak regelmatig commits met duidelijke messages
4. **Push** – Deel je werk via `git push`

## Cursor IDE

Dit project gebruikt Cursor als IDE. Na het openen van het project:
- De AI-assistent kent de projectstructuur
- Cursor rules (`.cursor/rules/`) bevatten project-specifieke instructies

## Hulp nodig?

- Lees eerst [START_APP.md](START_APP.md) – bevat oplossingen voor veelvoorkomende problemen
- Check de API docs op http://localhost:8000/docs
