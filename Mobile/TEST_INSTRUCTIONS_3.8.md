# Test Instructies - Stap 3.8: Device Management Screen

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

#### 3.1 Device Screen Basis Functionaliteit
- [ ] Screen laadt zonder errors
- [ ] Header toont "Device Beheer"
- [ ] Back button werkt
- [ ] Status card is zichtbaar
- [ ] Scan button is zichtbaar
- [ ] Device list is zichtbaar

#### 3.2 Bluetooth Status
- [ ] Bluetooth status wordt correct getoond
- [ ] Status color matcht state (rood/groen/oranje/blauw)
- [ ] Status text is correct:
  - "Bluetooth uit" als Bluetooth uit staat
  - "Verbonden met..." als connected
  - "Scannen naar devices..." tijdens scan
  - "Niet verbonden" als niet connected

#### 3.3 Device Scanning
- [ ] Scan button start scan
- [ ] Button text verandert naar "Stoppen..." tijdens scan
- [ ] Button color verandert naar rood tijdens scan
- [ ] Scan stopt na 15 seconden automatisch
- [ ] Scan kan handmatig gestopt worden
- [ ] Devices worden gevonden en getoond
- [ ] Empty state wordt getoond als geen devices gevonden

#### 3.4 Device Cards
- [ ] Device naam wordt getoond
- [ ] Device ID wordt getoond
- [ ] Signal strength (RSSI) wordt getoond
- [ ] Signal color matcht strength (groen/blauw/oranje/rood)
- [ ] Connected badge wordt getoond voor verbonden device
- [ ] Connect button is zichtbaar voor niet-verbonden devices
- [ ] Disconnect button is zichtbaar voor verbonden device

#### 3.5 Device Connection
- [ ] Tap op "Verbinden" start connection
- [ ] Loading indicator wordt getoond tijdens connect
- [ ] Connection success alert wordt getoond
- [ ] Device wordt gemarkeerd als verbonden
- [ ] Backend sync werkt (device wordt aangemaakt/geüpdatet)
- [ ] Error alert wordt getoond bij connection failure

#### 3.6 Device Disconnection
- [ ] Tap op "Verbinding verbreken" toont confirmatie alert
- [ ] Disconnect werkt correct
- [ ] Success alert wordt getoond
- [ ] Device status wordt geüpdatet
- [ ] Error handling werkt

#### 3.7 Connected Device Info
- [ ] Device ID wordt getoond in status card
- [ ] Battery level wordt getoond (indien beschikbaar)
- [ ] Battery level wordt elke 30 seconden geüpdatet
- [ ] Last seen timestamp wordt getoond
- [ ] Device info alert wordt getoond bij tap op verbonden device

#### 3.8 Backend Synchronization
- [ ] Device wordt aangemaakt in backend bij eerste connect
- [ ] Device wordt geüpdatet in backend bij volgende connects
- [ ] Device name wordt gesynchroniseerd
- [ ] Last seen wordt geüpdatet
- [ ] Error handling werkt (non-critical errors)

#### 3.9 Error Handling
- [ ] Bluetooth uit: alert wordt getoond
- [ ] Connection errors worden getoond
- [ ] Network errors worden afgehandeld
- [ ] Backend sync errors zijn non-critical

#### 3.10 Pull-to-Refresh
- [ ] Pull down refresht device list
- [ ] Scan wordt opnieuw gestart
- [ ] Loading indicator werkt

### 4. Backend Connectiviteit

#### 4.1 API Endpoints
- [ ] `GET /api/v1/devices/{device_id}` werkt
- [ ] `POST /api/v1/devices` werkt (device creation)
- [ ] `PATCH /api/v1/devices/{device_id}` werkt (device update)

#### 4.2 Data Format
- [ ] Device data wordt correct geparsed
- [ ] Metadata wordt correct opgeslagen
- [ ] Last seen wordt correct geüpdatet

### 5. Navigation Flow

#### 5.1 Van Dashboard
- [ ] Navigatie naar device screen werkt (via DeviceCard)
- [ ] Back button navigeert terug naar dashboard

#### 5.2 Van Quick Start
- [ ] Navigatie naar device screen werkt (als geen device connected)
- [ ] Back button navigeert terug

### 6. UI/UX Checks

#### 6.1 Layout
- [ ] Header is correct gepositioneerd
- [ ] Status card is goed zichtbaar
- [ ] Scan button is prominent
- [ ] Device list scrollt soepel
- [ ] Alles is goed zichtbaar

#### 6.2 Styling
- [ ] Themed components werken
- [ ] Icons zijn correct
- [ ] Colors zijn consistent
- [ ] Typography is correct
- [ ] Signal strength colors zijn duidelijk

#### 6.3 Responsiveness
- [ ] Layout werkt op verschillende schermformaten
- [ ] Scroll werkt soepel
- [ ] Touch targets zijn groot genoeg

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

## Test Flow

1. Start backend en MongoDB
2. Start mobile app
3. Navigeer naar Device Management screen
4. Test Bluetooth status:
   - Bluetooth aan/uit
   - Status indicators
5. Test device scanning:
   - Start scan
   - Stop scan
   - Verify devices worden gevonden
6. Test device connection:
   - Connect to device
   - Verify backend sync
   - Check battery level
7. Test device disconnection:
   - Disconnect device
   - Verify status update
8. Test error scenarios:
   - Bluetooth uit
   - Connection failures
   - Backend errors

## Known Issues / TODO

- [ ] Device name editing nog niet geïmplementeerd
- [ ] Device settings modal nog niet geïmplementeerd
- [ ] Better error messages kunnen worden toegevoegd
- [ ] Retry logic voor failed connections kan worden toegevoegd
