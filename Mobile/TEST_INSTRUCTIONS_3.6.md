# Test Instructies - Stap 3.6: Session Screen

## Test Checklist

### 1. TypeScript Compilatie
```bash
cd d:\Serena\Mobile
npx tsc --noEmit --skipLibCheck
```
- ✅ Geen TypeScript errors
- ✅ Alle imports correct

### 2. App Starten
```bash
cd d:\Serena\Mobile
npx expo start
```

### 3. Test Scenarios

#### 3.1 Session Screen Basis Functionaliteit
- [ ] Screen laadt zonder errors
- [ ] Header toont technique naam of "Ademhalingsoefening"
- [ ] Back button werkt
- [ ] Info button werkt
- [ ] Loading state wordt getoond tijdens fetch
- [ ] Empty state wordt getoond als geen sessie beschikbaar

#### 3.2 Breathing Ball Animation
- [ ] Breathing ball is zichtbaar
- [ ] Ball animatie werkt (in/out/hold)
- [ ] Ball beweegt soepel (60fps)
- [ ] Ball scale verandert met ademhaling
- [ ] Animatie loopt oneindig door
- [ ] Breath cycle wordt correct gelezen uit session metadata
- [ ] Default cycle (4s in, 4s out) wordt gebruikt als geen cycle beschikbaar

#### 3.3 Stats Cards
- [ ] Heart Rate (BPM) wordt getoond
- [ ] Actual Respiratory Rate wordt getoond
- [ ] Target Respiratory Rate wordt getoond (indien beschikbaar)
- [ ] Stats updaten real-time
- [ ] "--" wordt getoond als geen data beschikbaar
- [ ] Icons zijn correct (heart, lungs, target)

#### 3.4 Guidance Text
- [ ] Guidance text wordt getoond
- [ ] Color coding werkt (ok/warn/bad/accent)
- [ ] Border color matcht feedback color
- [ ] Audio text wordt getoond (indien verschillend van text)
- [ ] Placeholder wordt getoond als geen guidance

#### 3.5 Audio Feedback
- [ ] Audio toggle button is zichtbaar
- [ ] Audio kan aan/uit gezet worden
- [ ] Text-to-Speech werkt (indien audio aan)
- [ ] Audio wordt gestopt bij toggle uit
- [ ] Audio wordt niet afgespeeld als toggle uit
- [ ] Icon verandert (speaker.wave.2.fill / speaker.slash.fill)

#### 3.6 Session Controls
- [ ] Stop button is zichtbaar
- [ ] Stop button toont confirmatie alert
- [ ] Stop button beëindigt sessie
- [ ] Navigatie terug na stop werkt
- [ ] Error handling bij stop failure

#### 3.7 Real-time Updates
- [ ] SSE connection wordt gemaakt
- [ ] Real-time signal updates worden ontvangen
- [ ] Heart Rate updates real-time
- [ ] Respiratory Rate updates real-time
- [ ] Guidance updates real-time
- [ ] Stats cards updaten automatisch
- [ ] Breathing ball blijft animeren tijdens updates

#### 3.8 Navigation
- [ ] Navigatie naar session screen werkt (met sessionId parameter)
- [ ] Back button navigeert terug
- [ ] Info button toont technique info (tijdelijk alert)
- [ ] Navigatie na stop werkt

### 4. Backend Connectiviteit

#### 4.1 API Endpoints
- [ ] `GET /api/v1/sessions/{session_id}` werkt
- [ ] `POST /api/v1/sessions/{session_id}/end` werkt
- [ ] `GET /api/v1/stream` (SSE) werkt
- [ ] SSE stream levert signal data

#### 4.2 Data Format
- [ ] Session data wordt correct geparsed
- [ ] Breath cycle wordt correct gelezen uit metadata
- [ ] Signal data wordt correct verwerkt
- [ ] Guidance signals worden correct getoond

### 5. Component Tests

#### 5.1 BreathingBall Component
- [ ] Component laadt zonder errors
- [ ] Animatie start automatisch
- [ ] Animatie stopt bij unmount
- [ ] Breath cycle wordt correct gebruikt
- [ ] Default cycle wordt gebruikt als geen cycle beschikbaar
- [ ] Size en color props werken

#### 5.2 StatsCards Component
- [ ] Component laadt zonder errors
- [ ] Alle stats worden getoond
- [ ] Formatting is correct (BPM, bpm)
- [ ] Empty states werken

#### 5.3 GuidanceText Component
- [ ] Component laadt zonder errors
- [ ] Text wordt getoond
- [ ] Color coding werkt
- [ ] Border color matcht
- [ ] Placeholder wordt getoond

### 6. Hook Tests

#### 6.1 useSessionState Hook
- [ ] Hook laadt session data
- [ ] Active session wordt gevonden
- [ ] Real-time signals worden gestreamd
- [ ] Latest HR/RR worden opgehaald
- [ ] Latest guidance wordt opgehaald
- [ ] End session werkt

#### 6.2 useSignalStream Hook
- [ ] SSE client wordt aangemaakt
- [ ] Connection wordt gemaakt
- [ ] Signals worden ontvangen
- [ ] Error handling werkt
- [ ] Cleanup werkt bij unmount

### 7. Error Handling

#### 7.1 Network Errors
- [ ] Network errors worden getoond
- [ ] Retry logic werkt (indien geïmplementeerd)
- [ ] Graceful degradation

#### 7.2 Missing Data
- [ ] Geen sessie: empty state
- [ ] Geen stats: "--" wordt getoond
- [ ] Geen guidance: placeholder wordt getoond
- [ ] Geen breath cycle: default wordt gebruikt

### 8. Performance

#### 8.1 Animation Performance
- [ ] Breathing ball animatie is smooth (60fps)
- [ ] Geen frame drops
- [ ] Battery usage is acceptabel

#### 8.2 Memory Usage
- [ ] Geen memory leaks
- [ ] SSE connection wordt correct opgeruimd
- [ ] Component cleanup werkt

### 9. UI/UX Checks

#### 9.1 Layout
- [ ] Header is correct gepositioneerd
- [ ] Breathing ball is gecentreerd
- [ ] Stats cards zijn goed gespaced
- [ ] Guidance text is goed zichtbaar
- [ ] Controls zijn goed gepositioneerd

#### 9.2 Styling
- [ ] Themed components werken
- [ ] Icons zijn correct
- [ ] Colors zijn consistent
- [ ] Typography is correct

#### 9.3 Responsiveness
- [ ] Layout werkt op verschillende schermformaten
- [ ] Scroll werkt soepel
- [ ] Alles is goed zichtbaar

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

## Backend Requirements

Zorg dat de backend draait:
```bash
cd d:\Serena\Backend
# Start MongoDB (Docker)
docker-compose up -d mongodb

# Start FastAPI server
uvicorn app.main:app --reload
```

## Test Data Setup

### 1. Create Test Session
```bash
# Via API of via app
POST /api/v1/sessions
{
  "device_id": "test-device",
  "technique_name": "Test Technique",
  "param_version": "Default",
  "target_rr": 6.0,
  "metadata": {
    "breath_cycle": {
      "in": 4,
      "hold1": 0,
      "out": 4,
      "hold2": 0
    }
  }
}
```

### 2. Send Test Signals
```bash
# ECG signal
POST /api/v1/ingest
{
  "device_id": "test-device",
  "session_id": "<session_id>",
  "signal": "ecg",
  "ts": <timestamp>,
  "samples": [...]
}

# Heart Rate
POST /api/v1/ingest
{
  "device_id": "test-device",
  "session_id": "<session_id>",
  "signal": "hr_derived",
  "ts": <timestamp>,
  "bpm": 70
}

# Respiratory Rate
POST /api/v1/ingest
{
  "device_id": "test-device",
  "session_id": "<session_id>",
  "signal": "resp_rr",
  "ts": <timestamp>,
  "estRR": 6.5
}

# Guidance
POST /api/v1/ingest
{
  "device_id": "test-device",
  "session_id": "<session_id>",
  "signal": "guidance",
  "ts": <timestamp>,
  "text": "Goed bezig!",
  "audio_text": "Goed bezig!",
  "color": "ok"
}
```

## Known Issues / TODO

- [ ] Error alerts bij session creation failures
- [ ] Better error messages voor gebruiker
- [ ] Loading states kunnen verbeterd worden
- [ ] Breath cycle kan ook uit BreathTarget signal komen
- [ ] Technique info button navigeert nog niet naar detail

## Test Flow

1. Start backend en MongoDB
2. Start mobile app
3. Connect Bluetooth device (of gebruik test device)
4. Start session vanuit techniques screen
5. Navigeer naar session screen
6. Test alle functionaliteit:
   - Breathing ball animatie
   - Stats updates
   - Guidance updates
   - Audio feedback
   - Stop session
7. Test error scenarios:
   - Geen sessie
   - Geen data
   - Network errors
