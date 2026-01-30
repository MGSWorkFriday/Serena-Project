# Serena App starten – Frontend + Backend

Korte handleiding om **Backend** (FastAPI + MongoDB) en **Mobile** (Expo/React Native) te starten zodat alle functionaliteit (o.a. real-time visualisatie, Stap 3.11) werkt.

---

## 0. Eerste keer op jouw PC (setup)

Als je het project **voor het eerst** op je eigen Cursor/PC wilt draaien (bijv. overgenomen van een collega), doorloop dan onderstaande checklist. Daarna kun je sectie 1 t/m 6 gebruiken om te starten.

**Projectpad in deze docu:** `c:\proj\Serena-Project` (pas aan als jouw map anders heet).

### Checklist

| # | Wat | Actie |
|---|-----|--------|
| 1 | **Python** | Gebruik **3.11 of 3.12** (niet 3.13 i.v.m. motor/pymongo en numpy). Controle: `py -0` of `python --version`. Zo nodig: [python.org](https://www.python.org/downloads/) → 3.11.x of 3.12.x, bij install **“Add Python to PATH”** aanvinken. |
| 2 | **Node.js** | Voor Mobile (Expo). LTS 18 of 20. Controle: `node -v` en `npm -v`. Zo nodig: [nodejs.org](https://nodejs.org/). |
| 3 | **Docker Desktop** | Voor MongoDB. Installeer en start Docker Desktop; moet **draaien** vóór je de Backend start. Controle: `docker --version`. |
| 4 | **Backend – venv** | Eén keer: maak een virtual environment in de Backend-map. |
| 5 | **Backend – libraries** | Installeer Python-afhankelijkheden in die venv. |
| 6 | **Backend – .env** | Kopieer `.env.example` naar `.env` (optioneel; er zijn defaults). |
| 7 | **Mobile – libraries** | Installeer npm-pakketten in de Mobile-map. |
| 8 | **Mobile – .env** | Optioneel: kopieer `.env.example` naar `.env` voor API-URL (vooral nodig bij fysieke telefoon). |

### Uitvoeren (PowerShell)

```powershell
# --- Backend (eenmalig) ---
cd c:\proj\Serena-Project\Backend

# Python-versie controleren (moet 3.11 of 3.12 zijn)
python --version
# of: py -3.11 --version

# Virtual environment aanmaken
python -m venv venv
# of als je meerdere Python-versies hebt: py -3.11 -m venv venv

# Venv activeren
.\venv\Scripts\activate

# Dependencies installeren
python -m pip install --upgrade pip
pip install -r requirements.txt

# .env (optioneel)
copy .env.example .env
# Pas .env aan als je andere MongoDB-poort/credentials wilt

# --- Mobile (eenmalig) ---
cd c:\proj\Serena-Project\Mobile

npm install

# .env voor API-URL (optioneel; voor fysiek apparaat zie sectie 3)
copy .env.example .env
```

### Controleren

- **Python:** `python --version` → 3.11.x of 3.12.x  
- **Backend deps:** `cd Backend`, `.\venv\Scripts\activate`, `pip list` → o.a. fastapi, uvicorn, motor, pymongo, numpy, scipy  
- **Node:** `node -v`, `npm -v`  
- **Mobile deps:** `cd Mobile`, `npm list` (geen errors)  
- **Docker:** Docker Desktop open, daarna `docker ps` (mag leeg zijn, maar geen “cannot connect”)

Daarna: **sectie 1** (Backend starten) en **sectie 2** (Mobile starten). Bij problemen: **sectie 6** (Troubleshooting).

---

## Overzicht

| Component | Poort | Doel |
|-----------|-------|------|
| **MongoDB** | 27017 | Database |
| **Backend (FastAPI)** | 8000 | API, SSE-stream, techniques, sessions, etc. |
| **Mobile (Expo)** | 8081 (Metro) | App (device/simulator of web) |

De Mobile app praat met de Backend op `http://localhost:8000` (of je PC-IP op een fysiek apparaat).

---

## Na een reboot van je ontwikkel-PC

Na een herstart hoef je alleen dit te doen (geen venv/pip/npm install opnieuw):

| # | Wat | Actie |
|---|-----|--------|
| 1 | **Docker Desktop** | Start Docker Desktop en wacht tot het volledig opgestart is (icoon stabiel in systray). |
| 2 | **Backend** | Dubbelklik `start_backend.cmd` in de projectroot, of open een terminal en voer het uit. Laat het venster open (uvicorn draait daar). |
| 3 | **Mobile** | Dubbelklik `start_mobile.cmd` (of open een tweede terminal en voer het uit). Laat het venster open (Expo draait daar). |

De bestanden `start_backend.cmd` en `start_mobile.cmd` staan in `c:\proj\Serena-Project\`. Je kunt ze ook vanuit de projectroot in twee aparte terminals draaien.

---

## 1. Backend starten

### Vereisten

- **Python 3.11 of 3.12** (3.13 kan problemen geven met motor/pymongo)
- **Docker** (voor MongoDB) — **Docker Desktop moet draaien** vóór `docker-compose up`
- **Dependencies** in een venv

### Stappen

```powershell
# 1. Ga naar Backend
cd c:\proj\Serena-Project\Backend

# 2. (Eerste keer) Virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. (Eerste keer) Dependencies
pip install -r requirements.txt

# 4. (Eerste keer) .env – kopieer van voorbeeld (optioneel, er zijn defaults)
copy .env.example .env
# Pas .env aan als je andere MongoDB-credentials of poorten wilt

# 5. MongoDB starten
docker-compose up -d mongodb

# 6. Backend starten (moet vanuit de map Backend!)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Belangrijk:** Start uvicorn **altijd vanuit `c:\proj\Serena-Project\Backend`**. Als je vanuit `c:\proj\Serena-Project` (projectroot) start, krijg je `ModuleNotFoundError: No module named 'app'` — de module `app` staat in de Backend-map.

Backend is bereikbaar op:

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/healthz  

---

## 2. Mobile (Expo) starten

### Vereisten

- **Node.js** (LTS, bijv. 18 of 20)
- **npm** of **yarn**
- **Expo Go** op telefoon (bij fysiek apparaat) of Android/iOS-emulator

### Stappen

```powershell
# 1. Ga naar Mobile
cd c:\proj\Serena-Project\Mobile

# 2. (Eerste keer) Dependencies
npm install

# 3. (Optioneel) API-URL voor development
# Maak .env met:
#   EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
# Zonder .env gebruikt de app in __DEV__ standaard http://localhost:8000

# 4. App starten
npm start
# of: npx expo start
```

In het Expo-menu:

- **a** → Android-emulator  
- **i** → iOS-simulator (alleen op Mac)  
- **w** → Web  
- **Expo Go** → Scan QR-code met telefoon (zie hieronder voor API-URL)

---

## 3. API-URL voor fysiek apparaat

Op een **fysieke telefoon** is `localhost` het toestel zelf, niet je PC. De app moet dan naar het **IP van je computer** wijzen.

1. Zoek je lokale IP (bijv. `192.168.1.100`):
   ```powershell
   ipconfig
   ```
   Kijk bij je actieve adapter (Wi‑Fi of Ethernet) naar **IPv4-adres**.

2. Maak in `Mobile/` een `.env`:
   ```
   EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000
   ```
   Vervang `192.168.1.100` door jouw IP.

3. Zorg dat **Backend** op `0.0.0.0:8000` draait (zoals in de uvicorn-command) en dat **firewall** verkeer op poort 8000 toestaat.

4. Herstart Expo na het aanpassen van `.env`:
   ```powershell
   npx expo start
   ```

---

## 4. Controleren of alles werkt

1. **Backend**
   - http://localhost:8000/healthz → `{"status":"ok"}` of vergelijkbaar
   - http://localhost:8000/docs → Swagger UI

2. **Mobile**
   - Open de app (emulator of telefoon).
   - Ga naar **Settings** en controleer of de API-URL klopt (als je die daar toont).
   - Start een **sessie** of open schermen die **real-time data** (ECG, HR, RR) tonen → die halen data van `/api/v1/stream` en andere endpoints.

3. **Streaming / Stap 3.11**
   - De Backend moet draaien voor o.a.:
     - `GET /api/v1/stream` (SSE)
     - `GET /api/v1/signals/recent`
     - techniques, sessions, enz.
   - Zonder Backend werken alleen offline/gedeeltelijke functies.

---

## 5. Handige commands (kopieer & plak)

**Snel (na reboot):** dubbelklik `start_backend.cmd` en daarna `start_mobile.cmd` in de projectroot (zie [Na een reboot](#na-een-reboot-van-je-ontwikkel-pc)).

**Terminal 1 – Backend**

```powershell
cd c:\proj\Serena-Project\Backend
.\venv\Scripts\activate
docker-compose up -d mongodb
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – Mobile**

```powershell
cd c:\proj\Serena-Project\Mobile
npm start
```

---

## 6. Troubleshooting

| Probleem | Oplossing |
|----------|-----------|
| **`pip install -r requirements.txt` faalt** | Zie [Hieronder: pip install](#pip-install--r-requirementstxt-faalt). |
| **`open //./pipe/dockerDesktopLinuxEngine: ... Het systeem kan het opgegeven bestand niet vinden`** of **`unable to get image`** bij `docker-compose up` | **Docker Desktop draait niet.** Start Docker Desktop, wacht tot het volledig opgestart is, en voer `docker-compose up -d mongodb` opnieuw uit. |
| **`ModuleNotFoundError: No module named 'app'`** bij starten uvicorn | Je staat in de verkeerde map. Ga naar **Backend** en start dan opnieuw: `cd c:\proj\Serena-Project\Backend` (of `cd Backend` als je al in c:\proj\Serena-Project zit), daarna `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`. |
| MongoDB connection failed | `docker-compose up -d mongodb` opnieuw; `docker ps` om te zien of de container draait. |
| `ModuleNotFoundError` / importfouten in Backend | `pip install -r requirements.txt` in geactiveerde venv. |
| Motor/PyMongo fout (Python 3.13) | Python 3.11 of 3.12 gebruiken. |
| Mobile krijgt geen data van API | Backend op 8000? `.env` met `EXPO_PUBLIC_API_BASE_URL` correct? Op fysiek apparaat: IP i.p.v. localhost. |
| CORS-fout in browser (web) | Backend `CORS_ORIGINS` in `.env` / `config.py`: voeg `http://localhost:19006` (en eventueel je Expo-web-URL) toe. |

### `pip install -r requirements.txt` faalt

#### Fout: `Preparing metadata (pyproject.toml) ... error` bij **numpy**, of `Unknown compiler(s): [['cl'], ['gcc'], ...]`

Je gebruikt **Python 3.13**. Voor 3.13 bestaan er (nog) geen kant‑en‑klare Windows‑wheels voor numpy 1.26.x, dus pip probeert numpy uit bron te bouwen. Dat mislukt zonder C‑compiler (Visual Studio Build Tools).

**Oplossing: gebruik Python 3.11 of 3.12 en maak een nieuwe venv.**

1. **Python installeren** (als je die nog niet hebt):

   - **Aanbevolen: Python 3.11**  
     https://www.python.org/downloads/ → kies de nieuwste **3.11.x** (heeft nog gewone Windows‑installers). Bij installeren: **“Add Python to PATH”** aanvinken.

   - **Alternatief: Python 3.12.10** (laatste 3.12 met Windows‑installers)  
     https://www.python.org/downloads/release/python-31210/ → scroll naar **“Files”** → download bv. **“Windows installer (64-bit)”**. Bij installeren: **“Add Python to PATH”** aanvinken.  
     (Nieuwere 3.12.x releases hebben geen binary installers meer.)

2. **Oude venv verwijderen en nieuwe maken** met 3.11 of 3.12:

   **PowerShell:**
   ```powershell
   cd c:\proj\Serena-Project\Backend
   deactivate
   Remove-Item -Recurse -Force venv
   py -3.11 -m venv venv
   ```

   **Command Prompt (cmd):**
   ```cmd
   cd c:\proj\Serena-Project\Backend
   deactivate
   rmdir /s /q venv
   py -3.11 -m venv venv
   ```

   Voor 3.12: `py -3.12 -m venv venv`. Werkt `py` niet, gebruik het volledige pad, bv.  
   `C:\Users\Gebruiker\AppData\Local\Programs\Python\Python311\python.exe -m venv venv`

3. **Venv activeren en opnieuw installeren:**
   ```powershell
   .\venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Controleren:**
   ```powershell
   python --version
   ```
   Moet 3.11.x of 3.12.x zijn.

---

1. **Venv actief**  
   Zorg dat je in de Backend-venv zit:
   ```powershell
   cd c:\proj\Serena-Project\Backend
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Andere fout bij scipy/numpy (wel 3.11/3.12)**  
   - Eerst `numpy`, daarna `scipy`, daarna de rest:
     ```powershell
     pip install "numpy>=1.26.0,<2"
     pip install "scipy>=1.11"
     pip install -r requirements.txt
     ```
   - Of alleen binary builds (geen compilatie):
     ```powershell
     pip install --only-binary :all: numpy scipy
     pip install -r requirements.txt
     ```

3. **Fout bij motor/pymongo**  
   Vaak door Python 3.13. Gebruik Python 3.11 of 3.12 en een nieuwe venv (zie hierboven).

4. **Andere fout**  
   Stuur de **volledige foutmelding** (laatste 20–30 regels van `pip install -r requirements.txt`).

---

## 7. Optioneel: MongoDB Express

Voor een DB-UI (development):

```powershell
cd c:\proj\Serena-Project\Backend
docker-compose --profile tools up -d mongo-express
```

Daarna: http://localhost:8081 (login: admin/changeme, tenzij je dit in `.env` hebt gewijzigd).
