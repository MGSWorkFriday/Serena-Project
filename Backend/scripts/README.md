# Migration Scripts

## migrate_jsonl_to_mongodb.py

Migreert bestaande JSONL log bestanden naar MongoDB. Gebruikt **motor** (async).

### Python en dependencies

Gebruik de **zelfde Python** als de app (bijv. 3.12). Installeer dependencies in een **gewone CMD/PowerShell** (niet in Cursor, i.v.m. netwerk naar PyPI):

```bash
cd D:\Serena\Backend
python -m pip install -r requirements.txt
```

Daarna: `python scripts/migrate_jsonl_to_mongodb.py`

### Gebruik

```bash
# Zorg dat MongoDB draait
docker-compose up -d mongodb

# Run migration script
python scripts/migrate_jsonl_to_mongodb.py
```

### Wat wordt gemigreerd:

1. **JSONL Log Files** (`SerenaWebApp/pythonbleakgui_server/logs/`)
   - Device records (gecreëerd op basis van folder namen)
   - Session records (gecreëerd op basis van BreathTarget signalen)
   - Signal records (alle signal types: ECG, HR, RR, Guidance, etc.)

2. **Techniques** (`server/techniques.json`)
   - Alle ademhalingstechnieken

3. **Feedback Rules** (`server/feedback_rules.json`)
   - Feedback regels en instellingen

4. **Parameter Sets** (`resp_rr_param_sets.json`)
   - Algorithm parameter sets

### Output

Het script toont progress en een summary aan het einde:
- Aantal verwerkte bestanden
- Aantal devices, sessions, signals
- Aantal errors

### Technieken verschijnen niet in de app

De app haalt technieken via `GET /api/v1/techniques/public`; die route zoekt op `show_in_app: true` **en** `is_active: true`.

1. **Backend moet draaien** – "Offline" betekent dat de app de API niet bereikt. Start de Backend:
   ```bash
   cd D:\Serena\Backend
   docker-compose up -d
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **MongoDB bereikbaar** – Zelfde `docker-compose up -d` start MongoDB op 27017.
3. **Controleren in Compass** – Filter op de collectie `techniques`: `{ "show_in_app": true, "is_active": true }`. Alleen die documenten levert `/public`.
4. **Ontbrekende `is_active`** – Als je vóór een migratie-aanpassing hebt gemigreerd, kunnen docs `is_active` missen. In Compass (of mongosh) op database `serena`:
   ```javascript
   db.techniques.updateMany(
     { is_active: { $exists: false } },
     { $set: { is_active: true } }
   )
   ```
5. **API-URL in de app** – Voor web op localhost: de app gebruikt `http://localhost:8000`; de Backend moet op poort 8000 luisteren.
