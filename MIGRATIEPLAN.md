# Serena Applicatie Migratieplan

## Overzicht
Migratie van SerenaWebApp (FastAPI + HTML/JS) naar een moderne architectuur:
- **Backend**: FastAPI met MongoDB (Docker)
- **Frontend**: React Native (Expo) met TypeScript

---

## FASE 1: DATABASE MODELLEN (MongoDB)

### Stap 1.1: MongoDB Setup & Docker Configuratie
**Doel**: MongoDB database opzetten in Docker container

**Acties**:
- Maak `Backend/docker-compose.yml` aan met MongoDB service
- Configureer MongoDB met persistent volume
- Maak `Backend/.env.example` voor database connectie configuratie
- Documenteer connection string format

**Output**: 
- Docker compose bestand
- Environment variabelen template
- Database connectie configuratie

---

### Stap 1.2: Device Model
**Doel**: Opslag van device informatie en metadata

**Schema**:
```python
{
  "_id": ObjectId,
  "device_id": str,  # Bijv. "0A26843B"
  "name": str,  # Optioneel: gebruikersgegeven naam
  "type": str,  # "polar_h10", "custom", etc.
  "created_at": datetime,
  "last_seen": datetime,
  "metadata": dict  # Extra device-specifieke data
}
```

**Indexen**:
- `device_id` (unique)
- `last_seen` (voor cleanup queries)

---

### Stap 1.3: Session Model
**Doel**: Sessie tracking per device

**Schema**:
```python
{
  "_id": ObjectId,
  "device_id": str,
  "session_id": str,  # Unieke sessie identifier
  "started_at": datetime,
  "ended_at": datetime | null,
  "technique_name": str | null,  # Actieve ademtechniek
  "param_version": str,  # Parameter set versie
  "target_rr": float | null,  # Doel ademfrequentie
  "status": str,  # "active", "completed", "cancelled"
  "metadata": dict  # Extra sessie data
}
```

**Indexen**:
- `device_id` + `started_at` (compound)
- `session_id` (unique)
- `status` (voor actieve sessies query)

---

### Stap 1.4: Signal Record Model
**Doel**: Opslag van alle sensor data (ECG, HR, RR, etc.)

**Schema**:
```python
{
  "_id": ObjectId,
  "device_id": str,
  "session_id": str,  # Link naar Session
  "signal": str,  # "ecg", "hr_derived", "resp_rr", "guidance", "BreathTarget"
  "ts": int,  # Timestamp in milliseconds (epoch)
  "dt": str,  # Human-readable datetime: "DD-MM-YYYY HH:MM:SS:MMM"
  
  # Signal-specifieke velden (flexibel schema):
  "samples": [int] | null,  # Voor ECG signalen
  "bpm": float | null,  # Voor hr_derived
  "estRR": float | null,  # Voor resp_rr
  "tijd": str | null,  # Voor resp_rr
  "inhale": str | null,  # Voor resp_rr
  "exhale": str | null,  # Voor resp_rr
  
  # Guidance velden:
  "text": str | null,  # Visuele feedback tekst
  "audio_text": str | null,  # Audio feedback tekst
  "color": str | null,  # "ok", "warn", "bad", "accent"
  "target": float | null,  # Doel RR
  "actual": float | null,  # Actuele RR
  
  # BreathTarget velden:
  "TargetRR": float | null,
  "breath_cycle": dict | null,  # {in, hold1, out, hold2}
  "technique": str | null,
  "active_param_version": str | null,
  
  "created_at": datetime  # Server-side timestamp
}
```

**Indexen**:
- `device_id` + `ts` (compound, voor time-series queries)
- `session_id` + `signal` + `ts` (compound)
- `signal` + `ts` (voor signal-specifieke queries)
- `ts` (TTL index optioneel voor data retention)

**Overwegingen**:
- Gebruik Time Series Collection (MongoDB 5.0+) voor betere performance
- Of gebruik reguliere collection met goede indexering
- Overweeg data partitioning per maand/jaar voor grote volumes

---

### Stap 1.5: Technique Model
**Doel**: Ademhalingstechnieken opslag (vervangt techniques.json)

**Schema**:
```python
{
  "_id": ObjectId,
  "name": str,  # "Cyclic Sighing (Stanford-stijl)"
  "description": str,
  "param_version": str,  # "Default6", "Default5", etc.
  "show_in_app": bool,  # Of techniek zichtbaar is in mobile app
  "protocol": [[int]],  # Array van [in, hold1, out, hold2, cycles]
  "created_at": datetime,
  "updated_at": datetime,
  "is_active": bool  # Soft delete flag
}
```

**Indexen**:
- `name` (unique)
- `show_in_app` + `is_active` (voor public API queries)

---

### Stap 1.6: Feedback Rules Model
**Doel**: Feedback regels opslag (vervangt feedback_rules.json)

**Schema**:
```python
{
  "_id": ObjectId,
  "category": str,  # "blue", "green", "orange", "red_fast", "red_slow"
  "messages": [{
    "weight": int,
    "text": str,  # Visuele tekst
    "audio_text": str  # Audio tekst
  }],
  "threshold_sec": float | null,  # Voor "blue" categorie
  "threshold_pct": float | null,  # Voor andere categorieën
  "updated_at": datetime
}
```

**Of alternatief: Single Document Pattern**:
```python
{
  "_id": ObjectId,
  "rules": {
    "blue": {...},
    "green": {...},
    "orange": {...},
    "red_fast": {...},
    "red_slow": {...},
    "settings": {
      "stability_duration": float,
      "repeat_interval": float,
      "visual_interval": float
    }
  },
  "version": int,  # Voor optimistic locking
  "updated_at": datetime
}
```

**Indexen**:
- Single document pattern: geen indexen nodig (1 document)

---

### Stap 1.7: Parameter Set Model
**Doel**: Algorithm parameters opslag (vervangt resp_rr_param_sets.json)

**Schema**:
```python
{
  "_id": ObjectId,
  "version": str,  # "Default", "Default5", "Default6", etc.
  "BP_LOW_HZ": float,
  "BP_HIGH_HZ": float,
  "MWA_QRS_SEC": float,
  "MWA_BEAT_SEC": float,
  "MIN_SEG_SEC": float,
  "MIN_RR_SEC": float,
  "QRS_HALF_SEC": float,
  "HEARTBEAT_WINDOW": int,
  "FFT_LENGTH": int,
  "FREQ_RANGE_CB": [float, float],
  "SMOOTH_WIN": int,
  "BPM_MIN": float,
  "BPM_MAX": float,
  "HARMONIC_RATIO": float,
  "BUFFER_SIZE": int,
  "is_default": bool,
  "created_at": datetime
}
```

**Indexen**:
- `version` (unique)
- `is_default` (voor default parameter lookup)

---

### Stap 1.8: Data Migration Script
**Doel**: Migreer bestaande JSONL logs naar MongoDB

**Acties**:
- Script om JSONL bestanden te lezen uit `logs/` directory
- Parse elke regel en converteer naar Signal Record
- Extract device_id uit folder naam
- Maak Session documenten aan op basis van tijdstempels
- Batch insert voor performance
- Validatie en error handling
- Progress tracking

**Output**: 
- `Backend/scripts/migrate_jsonl_to_mongodb.py`
- Migration log bestand

---

## FASE 2: API ENDPOINTS (FastAPI)

### Stap 2.1: Project Structuur Setup
**Doel**: Nieuwe FastAPI project structuur

**Acties**:
- Maak `Backend/` directory structuur:
  ```
  Backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── database.py
  │   ├── models/          # Pydantic models
  │   ├── schemas/         # MongoDB document schemas
  │   ├── api/
  │   │   ├── __init__.py
  │   │   ├── v1/
  │   │   │   ├── __init__.py
  │   │   │   ├── devices.py
  │   │   │   ├── sessions.py
  │   │   │   ├── signals.py
  │   │   │   ├── techniques.py
  │   │   │   ├── feedback.py
  │   │   │   └── ingest.py
  │   ├── services/        # Business logic
  │   ├── utils/           # Helper functions
  │   └── algorithms/      # ECG processing (migreer resp_rr_estimator)
  ├── docker-compose.yml
  ├── Dockerfile
  ├── requirements.txt
  └── .env.example
  ```

---

### Stap 2.2: Database Connection & Models
**Doel**: MongoDB connectie en document models

**Acties**:
- Implementeer `database.py` met Motor (async MongoDB driver)
- Maak Pydantic models in `models/` voor request/response
- Maak MongoDB document schemas in `schemas/` (Beanie of custom)
- Setup connection pooling
- Error handling voor database connectie

**Bestanden**:
- `app/database.py`
- `app/models/device.py`
- `app/models/session.py`
- `app/models/signal.py`
- `app/models/technique.py`
- `app/models/feedback.py`
- `app/models/param_set.py`

---

### Stap 2.3: Health & System Endpoints
**Doel**: Basis health checks en systeem endpoints

**Endpoints**:
- `GET /healthz` - Health check
- `GET /api/v1/status` - Uitgebreide status (database, versie, etc.)

**Implementatie**: `app/api/v1/__init__.py` of `app/main.py`

---

### Stap 2.4: Device Management Endpoints
**Doel**: Device CRUD operaties

**Endpoints**:
- `GET /api/v1/devices` - Lijst alle devices
- `GET /api/v1/devices/{device_id}` - Device details
- `POST /api/v1/devices` - Registreer nieuw device
- `PATCH /api/v1/devices/{device_id}` - Update device metadata
- `GET /api/v1/devices/{device_id}/sessions` - Sessies van device

**Request/Response Models**:
```python
# Request
class DeviceCreate(BaseModel):
    device_id: str
    name: Optional[str] = None
    type: str = "polar_h10"

# Response
class DeviceResponse(BaseModel):
    device_id: str
    name: Optional[str]
    type: str
    created_at: datetime
    last_seen: datetime
```

**Implementatie**: `app/api/v1/devices.py`

---

### Stap 2.5: Session Management Endpoints
**Doel**: Sessie lifecycle management

**Endpoints**:
- `POST /api/v1/sessions` - Start nieuwe sessie
  - Body: `{device_id, technique_name?, param_version?}`
- `GET /api/v1/sessions/{session_id}` - Sessie details
- `PATCH /api/v1/sessions/{session_id}` - Update sessie (bijv. technique wijzigen)
- `POST /api/v1/sessions/{session_id}/end` - Stop sessie
- `GET /api/v1/sessions` - Lijst sessies (met filters: device_id, status, date range)

**Request/Response Models**:
```python
class SessionCreate(BaseModel):
    device_id: str
    technique_name: Optional[str] = None
    param_version: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    device_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    technique_name: Optional[str]
    status: str
```

**Implementatie**: `app/api/v1/sessions.py`

---

### Stap 2.6: Data Ingestion Endpoint
**Doel**: Sensor data ontvangen (vervangt huidige `/ingest`)

**Endpoint**:
- `POST /api/v1/ingest` - Accepteert NDJSON of JSON array

**Functionaliteit**:
- Parse incoming records (Record model)
- Valideer signal types
- Link records aan actieve sessie (via device_id)
- Trigger real-time processing (ECG → RR estimation)
- Store in MongoDB (Signal Record collection)
- Broadcast naar SSE subscribers
- Return accept count

**Request Model**:
```python
class RecordIngest(BaseModel):
    signal: str
    ts: Optional[Union[int, float]] = None
    device_id: Optional[str] = None
    # Extra fields allowed via Config.extra = "allow"
```

**Response Model**:
```python
class IngestResponse(BaseModel):
    accepted: int
    session_id: Optional[str] = None
```

**Processing Logic**:
- ECG signals → buffer in session → RR estimation → derived signals
- BreathTarget signals → update session target_rr
- Store all signals in database
- Real-time feedback generation

**Implementatie**: `app/api/v1/ingest.py` + `app/services/signal_processor.py`

---

### Stap 2.7: Real-time Streaming Endpoint
**Doel**: Server-Sent Events (SSE) voor live data

**Endpoint**:
- `GET /api/v1/stream` - SSE stream
  - Query params: `signals` (comma-separated), `device_id`, `session_id`

**Functionaliteit**:
- Subscribe op signal updates voor device/session
- Filter op signal types
- Send events als JSON: `data: {...}\n\n`
- Heartbeat mechanisme
- Auto-reconnect handling

**Implementatie**: 
- `app/api/v1/stream.py`
- `app/services/stream_manager.py` (vervangt SessionManager.broadcast)

**Verschil met oude implementatie**:
- Gebruik MongoDB Change Streams voor real-time updates
- Of in-memory pub/sub met Redis (optioneel voor schaalbaarheid)

---

### Stap 2.8: Signal Query Endpoints
**Doel**: Historische data ophalen

**Endpoints**:
- `GET /api/v1/signals` - Query signals met filters
  - Query params: `device_id`, `session_id`, `signal`, `start_ts`, `end_ts`, `limit`
- `GET /api/v1/signals/recent` - Recente signals (vervangt `/recent`)
  - Query params: `signal`, `device_id`, `limit` (default 300)
- `GET /api/v1/signals/{signal_id}` - Single signal record

**Response Format**:
```python
class SignalResponse(BaseModel):
    signal: str
    ts: int
    dt: str
    device_id: str
    session_id: Optional[str]
    # Signal-specifieke velden...
```

**Implementatie**: `app/api/v1/signals.py`

---

### Stap 2.9: Techniques Management Endpoints
**Doel**: Ademhalingstechnieken CRUD

**Endpoints**:
- `GET /api/v1/techniques` - Alle technieken (admin)
- `GET /api/v1/techniques/public` - Alleen `show_in_app=true` technieken
- `GET /api/v1/techniques/{name}` - Techniek details
- `POST /api/v1/techniques` - Maak/update techniek
- `DELETE /api/v1/techniques/{name}` - Verwijder techniek (soft delete)

**Request/Response Models**:
```python
class TechniqueCreate(BaseModel):
    name: str
    description: str
    param_version: str
    show_in_app: bool = False
    protocol: List[List[int]]  # [[in, hold1, out, hold2, cycles], ...]

class TechniqueResponse(BaseModel):
    name: str
    description: str
    param_version: str
    show_in_app: bool
    protocol: List[List[int]]
```

**Implementatie**: `app/api/v1/techniques.py`

---

### Stap 2.10: Feedback Rules Endpoints
**Doel**: Feedback regels beheer

**Endpoints**:
- `GET /api/v1/feedback/rules` - Haal alle regels op
- `POST /api/v1/feedback/rules` - Update regels
- `GET /api/v1/feedback/rules/settings` - Alleen settings

**Request/Response**: Single document pattern (zie Database Model 1.6)

**Implementatie**: `app/api/v1/feedback.py`

---

### Stap 2.11: Parameter Sets Endpoints
**Doel**: Algorithm parameters beheer

**Endpoints**:
- `GET /api/v1/param_versions` - Lijst alle versies
- `GET /api/v1/param_versions/{version}` - Parameter set details
- `POST /api/v1/param_versions` - Maak nieuwe parameter set
- `PATCH /api/v1/param_versions/{version}` - Update parameter set

**Implementatie**: `app/api/v1/param_sets.py`

---

### Stap 2.12: Algorithm Processing Service
**Doel**: ECG → RR estimation logica migreren

**Acties**:
- Migreer `resp_rr_estimator.py` naar `app/algorithms/resp_rr_estimator.py`
- Migreer `resp_rr_param_sets.py` logica
- Integreer met MongoDB parameter sets
- Async processing voor real-time data
- Buffer management per session (vervang DeviceSession.ecg_buffer)

**Implementatie**: 
- `app/services/signal_processor.py`
- `app/algorithms/resp_rr_estimator.py`
- `app/algorithms/feedback_generator.py` (migreer feedback_engine.py)

---

### Stap 2.13: CORS & Security
**Doel**: CORS configuratie voor mobile app

**Acties**:
- Configureer CORS middleware voor Expo development
- Environment-based CORS origins
- API key authentication (optioneel)
- Rate limiting (optioneel)

**Implementatie**: `app/main.py` middleware setup

---

### Stap 2.14: Error Handling & Logging
**Doel**: Gestructureerde error handling

**Acties**:
- Custom exception classes
- Error response models
- Structured logging (JSON format)
- Request/response logging middleware

**Implementatie**: `app/utils/exceptions.py`, `app/utils/logging.py`

---

## FASE 3: UI SCHERMEN (React Native / Expo)

### Stap 3.1: Project Setup & Dependencies
**Doel**: Expo project configureren met benodigde packages

**Acties**:
- Update `Mobile/package.json` met dependencies:
  - `@react-native-async-storage/async-storage` - Local storage
  - `react-native-ble-plx` - Bluetooth Low Energy (Polar H10)
  - `expo-av` - Audio playback (voor feedback)
  - `react-native-reanimated` - Animaties (al aanwezig)
  - `@tanstack/react-query` - Data fetching & caching
  - `axios` of `fetch` - API calls
  - `date-fns` - Date formatting
- Configureer app.json voor permissions (Bluetooth, etc.)
- Setup TypeScript strict mode
- Environment variabelen voor API URL

**Bestanden**:
- `Mobile/package.json`
- `Mobile/app.json`
- `Mobile/.env.example`

---

### Stap 3.2: API Client Layer
**Doel**: Type-safe API client voor backend communicatie

**Acties**:
- Maak `Mobile/services/api/` directory
- Implementeer API client met TypeScript interfaces
- Request/response type definitions
- Error handling
- Token management (indien nodig)
- SSE client voor real-time streaming

**Bestanden**:
- `Mobile/services/api/client.ts`
- `Mobile/services/api/types.ts`
- `Mobile/services/api/endpoints.ts`
- `Mobile/services/api/sse.ts` - Server-Sent Events client

**Type Definitions**:
```typescript
interface Device {
  device_id: string;
  name?: string;
  type: string;
  created_at: string;
  last_seen: string;
}

interface Session {
  session_id: string;
  device_id: string;
  started_at: string;
  ended_at?: string;
  technique_name?: string;
  status: 'active' | 'completed' | 'cancelled';
}

interface SignalRecord {
  signal: string;
  ts: number;
  dt: string;
  device_id: string;
  session_id?: string;
  // Signal-specifieke velden...
}
```

---

### Stap 3.3: Bluetooth Service (Polar H10)
**Doel**: Bluetooth Low Energy connectie met Polar H10

**Acties**:
- Implementeer BLE service wrapper
- Device scanning
- Connect/disconnect logic
- ECG data subscription
- Data parsing en formatting
- Error handling en reconnection logic
- Permissions handling (Android/iOS verschillen)

**Bestanden**:
- `Mobile/services/bluetooth/polarService.ts`
- `Mobile/services/bluetooth/types.ts`
- `Mobile/hooks/useBluetooth.ts` - React hook voor BLE state

**Verschillen Web vs Mobile**:
- Web: Web Bluetooth API (beperkt browser support)
- Mobile: Native BLE via react-native-ble-plx (volledige controle)
- Mobile heeft betere background support

---

### Stap 3.4: Navigation Setup
**Doel**: App navigatie structuur

**Acties**:
- Setup Expo Router (al aanwezig)
- Definieer navigatie routes:
  - `/` - Home/Dashboard
  - `/session` - Actieve sessie scherm
  - `/techniques` - Technieken selectie
  - `/history` - Sessie geschiedenis
  - `/settings` - Instellingen
  - `/device` - Device management
- Tab navigatie voor hoofdschermen
- Stack navigatie voor detail schermen

**Bestanden**:
- `Mobile/app/_layout.tsx` (update)
- `Mobile/app/(tabs)/_layout.tsx` (update)
- Nieuwe screen bestanden

---

### Stap 3.5: Home/Dashboard Screen
**Doel**: Hoofdscherm met overzicht en quick actions

**Componenten**:
- Device status card (connected/disconnected)
- Quick start button
- Recent sessions list
- Current stats (laatste HR, RR)
- Navigation naar andere schermen

**Features**:
- Real-time device status
- Last session summary
- Quick technique selection

**Bestanden**:
- `Mobile/app/(tabs)/index.tsx` (update)
- `Mobile/components/dashboard/DeviceCard.tsx`
- `Mobile/components/dashboard/QuickStart.tsx`
- `Mobile/components/dashboard/RecentSessions.tsx`

**Verschillen Web vs Mobile**:
- Web: Single page met alles zichtbaar
- Mobile: Card-based layout, scrollable, touch-optimized
- Mobile: Swipe gestures voor acties

---

### Stap 3.6: Session Screen (Actieve Oefening)
**Doel**: Hoofdscherm tijdens actieve ademhalingsoefening

**Componenten**:
- **Breathing Ball Animation** (vervangt canvas)
  - React Native Reanimated voor smooth animaties
  - SVG of native View animaties
  - Real-time size/position updates
- **Stats Cards**:
  - Heart Rate (BPM)
  - Actual Respiratory Rate
  - Target Respiratory Rate
- **Guidance Text**:
  - Color-coded feedback tekst
  - Audio feedback (Text-to-Speech of pre-recorded)
- **ECG Waveform** (optioneel):
  - Line chart component (react-native-chart-kit of victory-native)
  - Real-time data updates
- **Controls**:
  - Stop button
  - Technique info button
  - Audio toggle

**State Management**:
- React Query voor signal data
- SSE subscription voor real-time updates
- Local state voor UI animaties

**Bestanden**:
- `Mobile/app/session.tsx` (nieuw)
- `Mobile/components/session/BreathingBall.tsx`
- `Mobile/components/session/StatsCards.tsx`
- `Mobile/components/session/GuidanceText.tsx`
- `Mobile/components/session/ECGChart.tsx` (optioneel)
- `Mobile/hooks/useSession.ts`
- `Mobile/hooks/useSignalStream.ts`

**Verschillen Web vs Mobile**:
- **Canvas → Native Animations**: Web gebruikt HTML5 Canvas, Mobile gebruikt React Native Reanimated of native View animaties
- **Audio**: Web gebruikt Web Audio API, Mobile gebruikt expo-av of react-native-sound
- **Layout**: Web heeft meer ruimte, Mobile moet compact zijn met swipeable sections
- **Performance**: Mobile heeft betere native performance voor animaties
- **Background**: Mobile kan background processing (met beperkingen)

---

### Stap 3.7: Technique Selection Screen
**Doel**: Ademhalingstechniek kiezen

**Componenten**:
- Technique list (filter op `show_in_app=true`)
- Technique card met:
  - Naam
  - Beschrijving
  - Protocol preview (in/out/hold tijden)
  - Info button
- Search/filter functionaliteit
- Technique detail modal

**Bestanden**:
- `Mobile/app/(tabs)/techniques.tsx` (nieuw)
- `Mobile/components/techniques/TechniqueCard.tsx`
- `Mobile/components/techniques/TechniqueDetailModal.tsx`
- `Mobile/hooks/useTechniques.ts`

**Verschillen Web vs Mobile**:
- Web: Dropdown select
- Mobile: Full-screen list met cards, swipeable, search bar
- Mobile: Pull-to-refresh

---

### Stap 3.8: Device Management Screen
**Doel**: Bluetooth device connectie beheer

**Componenten**:
- Device scan button
- Available devices list
- Connected device status
- Device info (ID, naam, type)
- Connect/disconnect buttons
- Device settings (optioneel: naam wijzigen)

**Bestanden**:
- `Mobile/app/device.tsx` (nieuw)
- `Mobile/components/device/DeviceList.tsx`
- `Mobile/components/device/DeviceCard.tsx`
- `Mobile/hooks/useDeviceScan.ts`

**Verschillen Web vs Mobile**:
- Web: Web Bluetooth API (beperkt)
- Mobile: Native BLE met volledige device discovery
- Mobile: Better permission handling
- Mobile: Background connection support

---

### Stap 3.9: Session History Screen
**Doel**: Overzicht van eerdere sessies

**Componenten**:
- Session list (chronologisch)
- Session card met:
  - Datum/tijd
  - Duur
  - Techniek naam
  - Gemiddelde stats (HR, RR)
- Filter op datum/techniek
- Session detail view (tap voor details)
- Export functionaliteit (optioneel)

**Bestanden**:
- `Mobile/app/(tabs)/history.tsx` (nieuw)
- `Mobile/components/history/SessionCard.tsx`
- `Mobile/components/history/SessionDetail.tsx`
- `Mobile/hooks/useSessions.ts`

**Verschillen Web vs Mobile**:
- Web: Mogelijk geen history scherm (alleen real-time)
- Mobile: Dedicated history met pull-to-refresh, infinite scroll
- Mobile: Share functionaliteit voor exports

---

### Stap 3.10: Settings Screen
**Doel**: App instellingen

**Componenten**:
- Audio feedback toggle
- Feedback rules settings (indien admin)
- Parameter version selectie (indien admin)
- API URL configuratie (development)
- About/Version info
- Logout/Clear data (indien auth toegevoegd)

**Bestanden**:
- `Mobile/app/(tabs)/settings.tsx` (nieuw)
- `Mobile/components/settings/SettingsList.tsx`
- `Mobile/hooks/useSettings.ts`
- `Mobile/services/storage.ts` (AsyncStorage wrapper)

---

### Stap 3.11: Real-time Data Visualization
**Doel**: Live charts en visualisaties

**Componenten**:
- **ECG Waveform Chart**:
  - Line chart met real-time updates
  - Scrollable time window
  - Zoom/pan (optioneel)
- **Respiratory Rate Chart**:
  - Line chart met target vs actual
  - Color-coded zones (green/orange/red)
- **Heart Rate Chart**:
  - Real-time BPM line

**Libraries**:
- `react-native-chart-kit` of
- `victory-native` of
- `react-native-svg` + custom drawing

**Bestanden**:
- `Mobile/components/charts/ECGChart.tsx`
- `Mobile/components/charts/RRChart.tsx`
- `Mobile/components/charts/HRChart.tsx`
- `Mobile/hooks/useChartData.ts`

**Verschillen Web vs Mobile**:
- Web: HTML5 Canvas voor custom drawing
- Mobile: SVG-based charts of native chart libraries
- Mobile: Touch gestures voor interactie (zoom, pan)
- Performance: Mobile heeft betere native rendering

---

### Stap 3.12: Breathing Ball Animation
**Doel**: Animaties voor ademhalingsoefening

**Implementatie Opties**:
1. **React Native Reanimated** (aanbevolen):
   - Smooth 60fps animaties
   - Native driver voor performance
   - Complex timing curves
2. **React Native SVG + Animated**:
   - SVG paths voor golf
   - Animated API voor beweging
3. **Lottie** (optioneel):
   - Pre-made animaties
   - Minder flexibel

**Features**:
- Ball beweging (in/out/hold)
- Waveform achtergrond
- Color transitions (op basis van feedback)
- Smooth timing gebaseerd op breath_cycle

**Bestanden**:
- `Mobile/components/session/BreathingBall.tsx`
- `Mobile/utils/breathingAnimation.ts` - Timing calculations

**Verschillen Web vs Mobile**:
- Web: Canvas-based met requestAnimationFrame
- Mobile: Native animations met Reanimated (betere performance, battery efficiency)
- Mobile: Haptic feedback mogelijk (expo-haptics)

---

### Stap 3.13: Audio Feedback
**Doel**: Text-to-Speech of audio playback

**Implementatie**:
- `expo-speech` voor Text-to-Speech
- Of `expo-av` voor pre-recorded audio files
- Audio queue management
- Volume control
- Mute/unmute toggle

**Bestanden**:
- `Mobile/services/audio/audioService.ts`
- `Mobile/hooks/useAudioFeedback.ts`

**Verschillen Web vs Mobile**:
- Web: Web Speech API
- Mobile: Native TTS (betere kwaliteit, meer talen)
- Mobile: Background audio mogelijk (met beperkingen)

---

### Stap 3.14: State Management & Data Flow
**Doel**: Centralized state management

**Opties**:
1. **React Query** (aanbevolen):
   - Server state management
   - Caching & synchronization
   - Real-time updates via SSE
2. **Zustand** (optioneel):
   - Client state (UI state, device connection)
   - Lightweight, simple API
3. **Context API** (voor globale state):
   - Theme, settings, etc.

**Implementatie**:
- React Query voor API data
- Custom hooks voor business logic
- Local state voor UI-only state

**Bestanden**:
- `Mobile/services/queryClient.ts`
- `Mobile/hooks/useSessionState.ts`
- `Mobile/hooks/useDeviceState.ts`

---

### Stap 3.15: Error Handling & Offline Support
**Doel**: Graceful error handling en offline mode

**Features**:
- Network error detection
- Offline queue voor data ingest (store locally, sync later)
- Error boundaries
- User-friendly error messages
- Retry logic

**Bestanden**:
- `Mobile/components/ErrorBoundary.tsx`
- `Mobile/services/offlineQueue.ts`
- `Mobile/hooks/useNetworkStatus.ts`

---

### Stap 3.16: Theming & Styling
**Doel**: Consistent design system

**Acties**:
- Define color scheme (match web app)
- Typography system
- Component library setup
- Dark mode support (optioneel)
- Responsive design (tablets)

**Bestanden**:
- `Mobile/constants/theme.ts` (update)
- `Mobile/constants/colors.ts`
- `Mobile/components/ui/` (reusable components)

---

### Stap 3.17: Testing & Polish
**Doel**: App testing en optimalisaties

**Acties**:
- Unit tests voor services
- Integration tests voor API calls
- E2E tests voor kritieke flows (optioneel)
- Performance profiling
- Memory leak detection
- Battery usage optimization
- App store assets (icons, splash screens)

---

## FASE 4: INTEGRATIE & TESTING

### Stap 4.1: End-to-End Integration
**Doel**: Volledige flow testen

**Test Scenarios**:
1. Device connectie → Sessie start → Data ingest → Real-time updates → Sessie stop
2. Technique selectie → Sessie start → Feedback ontvangen
3. History bekijken → Session details
4. Offline mode → Data queue → Sync wanneer online

---

### Stap 4.2: Performance Testing
**Doel**: Performance optimalisaties

**Metingen**:
- API response times
- Real-time stream latency
- Mobile app frame rate (60fps voor animaties)
- Battery usage
- Memory usage
- Database query performance

---

### Stap 4.3: Data Migration Validation
**Doel**: Verifieer data migratie

**Acties**:
- Compare JSONL data met MongoDB records
- Validate signal counts
- Check timestamp accuracy
- Verify device/session linking

---

## FASE 5: DEPLOYMENT

### Stap 5.1: Backend Deployment
**Doel**: Backend in productie

**Acties**:
- Docker image build
- Environment configuratie
- MongoDB backup strategy
- Monitoring & logging setup
- API documentation (Swagger/OpenAPI)

---

### Stap 5.2: Mobile App Deployment
**Doel**: App store releases

**Acties**:
- Expo build configuration
- iOS App Store setup
- Google Play Store setup
- OTA updates configuratie (Expo Updates)
- Version management

---

## BELANGRIJKE VERSCHILLEN WEB vs MOBILE

### 1. Bluetooth Connectivity
- **Web**: Web Bluetooth API (Chrome/Edge only, beperkte features)
- **Mobile**: Native BLE (volledige controle, betere background support)

### 2. Real-time Visualizations
- **Web**: HTML5 Canvas (DOM-based)
- **Mobile**: Native animations (Reanimated) of SVG charts (betere performance)

### 3. Audio Feedback
- **Web**: Web Speech API (browser-dependent)
- **Mobile**: Native TTS (betere kwaliteit, meer talen)

### 4. Layout & Navigation
- **Web**: Single page, scrollable
- **Mobile**: Multi-screen met tab/stack navigation, touch-optimized

### 5. Data Storage
- **Web**: LocalStorage, IndexedDB
- **Mobile**: AsyncStorage, SQLite (via expo-sqlite indien nodig)

### 6. Background Processing
- **Web**: Service Workers (beperkt)
- **Mobile**: Native background tasks (met OS beperkingen)

### 7. Performance
- **Web**: DOM rendering, JavaScript execution
- **Mobile**: Native rendering, betere animatie performance

---

## MIGRATIE CHECKLIST

### Database
- [ ] MongoDB Docker setup
- [ ] Alle models geïmplementeerd
- [ ] Indexen aangemaakt
- [ ] Data migratie script getest
- [ ] Backup strategy geïmplementeerd

### Backend API
- [ ] Alle endpoints geïmplementeerd
- [ ] Request/response models gedefinieerd
- [ ] Error handling compleet
- [ ] CORS geconfigureerd
- [ ] Real-time streaming werkend
- [ ] Algorithm processing gemigreerd
- [ ] Tests geschreven

### Mobile App
- [ ] Navigation setup
- [ ] API client geïmplementeerd
- [ ] Bluetooth service werkend
- [ ] Alle screens geïmplementeerd
- [ ] Real-time updates werkend
- [ ] Animaties smooth (60fps)
- [ ] Audio feedback werkend
- [ ] Offline support geïmplementeerd
- [ ] Error handling compleet
- [ ] Theming consistent

### Integration
- [ ] End-to-end flow getest
- [ ] Performance geoptimaliseerd
- [ ] Data migratie gevalideerd
- [ ] Documentation compleet

---

## VOLGENDE STAPPEN

1. Begin met Database Models (Fase 1)
2. Implementeer Backend API (Fase 2)
3. Test Backend met Postman/Thunder Client
4. Start Mobile App development (Fase 3)
5. Integreer en test volledige flow
6. Deploy naar productie

---

**Laatste update**: 2026-01-23
**Versie**: 1.0
