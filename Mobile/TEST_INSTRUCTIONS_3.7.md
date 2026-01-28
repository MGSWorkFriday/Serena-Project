# Test Instructies - Stap 3.7: Technique Selection Screen

## Test Checklist

### 1. TypeScript Compilatie
```bash
cd d:\Serena\Mobile
npx tsc --noEmit --skipLibCheck
```
- ✅ Geen TypeScript errors
- ✅ Alle imports correct
- ✅ Types correct gedefinieerd

### 2. App Starten
```bash
cd d:\Serena\Mobile
npx expo start
```

### 3. Test Scenarios

#### 3.1 Techniques Screen Basis Functionaliteit
- [ ] Screen laadt zonder errors
- [ ] Header toont "Ademhalingstechnieken"
- [ ] Search bar is zichtbaar
- [ ] Loading state wordt getoond tijdens fetch
- [ ] Techniques worden geladen en getoond
- [ ] Empty state wordt getoond als geen technieken beschikbaar

#### 3.2 Search Functionaliteit
- [ ] Typen in search bar filtert technieken
- [ ] Search werkt op naam
- [ ] Search werkt op beschrijving
- [ ] Clear button verschijnt bij input
- [ ] Clear button wist search query
- [ ] Empty state bij geen resultaten

#### 3.3 Technique Cards
- [ ] Cards tonen techniek naam
- [ ] Cards tonen beschrijving (indien beschikbaar)
- [ ] Cards tonen protocol preview
- [ ] Info button is zichtbaar
- [ ] Tap op card opent detail modal
- [ ] Tap op info button opent detail modal

#### 3.4 Technique Detail Modal
- [ ] Modal opent bij tap op card
- [ ] Modal toont volledige techniek naam
- [ ] Modal toont beschrijving
- [ ] Modal toont protocol breakdown
- [ ] Modal toont metadata (param_version, status)
- [ ] Close button sluit modal
- [ ] Swipe down sluit modal (indien ondersteund)

#### 3.5 Session Creation
- [ ] "Start Sessie" button is zichtbaar (indien device connected)
- [ ] Button is disabled als geen device connected
- [ ] Tap op "Start Sessie" creëert session
- [ ] Navigatie naar session screen werkt
- [ ] Session wordt correct aangemaakt met technique data

#### 3.6 Pull-to-Refresh
- [ ] Pull down refresht techniques list
- [ ] Loading indicator tijdens refresh
- [ ] Data wordt opnieuw geladen

#### 3.7 Error Handling
- [ ] Network error wordt getoond
- [ ] Empty state bij geen data
- [ ] Loading states werken correct

### 4. Backend Connectiviteit

#### 4.1 API Endpoints
- [ ] `GET /api/v1/techniques/public` werkt
- [ ] Response bevat `show_in_app=true` technieken
- [ ] Response format is correct

#### 4.2 Data Format
- [ ] Protocol format is correct: `[[in, hold1, out, hold2, repeats], ...]`
- [ ] `param_version` field is aanwezig
- [ ] `description` field wordt correct getoond

### 5. Navigation Flow

#### 5.1 Van Home Screen
- [ ] Navigatie naar techniques tab werkt
- [ ] Quick Start button navigeert naar techniques (indien device connected)

#### 5.2 Van Techniques naar Session
- [ ] Selectie van techniek
- [ ] Tap op "Start Sessie"
- [ ] Navigatie naar `/session` met `sessionId` parameter
- [ ] Session screen laadt correct

### 6. UI/UX Checks

#### 6.1 Layout
- [ ] Header is correct gepositioneerd
- [ ] Search bar is goed zichtbaar
- [ ] Cards zijn goed gespaced
- [ ] Modal overlay werkt correct

#### 6.2 Styling
- [ ] Themed components werken (dark/light mode)
- [ ] Icons zijn correct
- [ ] Colors zijn consistent
- [ ] Typography is correct

#### 6.3 Responsiveness
- [ ] Layout werkt op verschillende schermformaten
- [ ] Scroll werkt soepel
- [ ] Modal past zich aan scherm aan

### 7. Known Issues / TODO

- [ ] Error alerts bij session creation failures
- [ ] Better error messages voor gebruiker
- [ ] Loading states kunnen verbeterd worden
- [ ] Protocol formatting kan robuuster

## Test Commands

### Start Development Server
```bash
cd d:\Serena\Mobile
npx expo start
```

### Check TypeScript
```bash
cd d:\Serena\Mobile
npx tsc --noEmit --skipLibCheck
```

### Check Linter
```bash
cd d:\Serena\Mobile
npm run lint  # if available
```

## Backend Requirements

Zorg dat de backend draait:
```bash
cd d:\Serena\Backend
# Start MongoDB (Docker)
docker-compose up -d mongodb

# Start FastAPI server
uvicorn app.main:app --reload
```

## Test Data

Zorg dat er test technieken zijn in de database met:
- `show_in_app: true`
- Protocol data: `[[in, hold1, out, hold2, repeats], ...]`
- Beschrijvingen
- Verschillende param_versions
