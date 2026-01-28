# Test Instructies - Stap 3.11: Real-time Data Visualization

## ⚠️ Status

**Stap 3.11 is nog NIET geïmplementeerd.**

Volgens `FASE3_STATUS.md`:
- ❌ ECG Waveform Chart niet geïmplementeerd
- ❌ Respiratory Rate Chart niet geïmplementeerd
- ❌ Heart Rate Chart niet geïmplementeerd
- ❌ Chart libraries nog niet geïnstalleerd
- ❌ useChartData hook niet gemaakt

## 📋 Wat Moet Worden Geïmplementeerd

### Componenten
1. **ECGChart Component** (`components/charts/ECGChart.tsx`)
   - Line chart met real-time ECG waveform
   - Scrollable time window
   - Zoom/pan functionaliteit (optioneel)

2. **RRChart Component** (`components/charts/RRChart.tsx`)
   - Line chart met target vs actual respiratory rate
   - Color-coded zones (green/orange/red)
   - Real-time updates

3. **HRChart Component** (`components/charts/HRChart.tsx`)
   - Real-time BPM line chart
   - Time-based visualization

4. **useChartData Hook** (`hooks/useChartData.ts`)
   - Data processing voor charts
   - Time window management
   - Signal buffering

### Chart Libraries

Er moet een chart library worden geïnstalleerd. Opties:
- `react-native-chart-kit` - Eenvoudig, maar beperkt
- `victory-native` - Krachtig, veel features
- `react-native-svg` + custom drawing - Volledige controle

### Integratie

Charts moeten worden geïntegreerd in:
- Session Screen (`app/session.tsx`) - voor real-time visualisatie tijdens sessie
- Session Detail (`components/history/SessionDetail.tsx`) - voor historische data

## 🧪 Test Plan (Na Implementatie)

### 1. ECG Chart Tests
- [ ] Chart wordt getoond op session screen
- [ ] Real-time ECG data wordt getoond
- [ ] Time window scrollt correct
- [ ] Performance is acceptabel (60fps)
- [ ] Zoom functionaliteit werkt (indien geïmplementeerd)
- [ ] Pan functionaliteit werkt (indien geïmplementeerd)

### 2. RR Chart Tests
- [ ] Chart wordt getoond op session screen
- [ ] Target RR lijn wordt getoond
- [ ] Actual RR lijn wordt getoond
- [ ] Color-coded zones werken (green/orange/red)
- [ ] Real-time updates werken
- [ ] Data points worden correct weergegeven

### 3. HR Chart Tests
- [ ] Chart wordt getoond op session screen
- [ ] Real-time BPM wordt getoond
- [ ] Time-based visualization werkt
- [ ] Updates zijn smooth

### 4. Data Integration Tests
- [ ] Charts ontvangen data van useSignalStream
- [ ] Data wordt correct geparsed
- [ ] Time window management werkt
- [ ] Buffer management werkt correct
- [ ] Memory leaks worden voorkomen

### 5. Performance Tests
- [ ] Charts renderen zonder lag
- [ ] Real-time updates zijn smooth
- [ ] Memory usage blijft stabiel
- [ ] Battery usage is acceptabel

## 📝 Implementatie Checklist

Voordat we kunnen testen, moet het volgende worden geïmplementeerd:

### Setup
- [ ] Installeer chart library (bijv. `victory-native`)
- [ ] Update `package.json`
- [ ] Configureer native dependencies (indien nodig)

### Components
- [ ] Maak `components/charts/ECGChart.tsx`
- [ ] Maak `components/charts/RRChart.tsx`
- [ ] Maak `components/charts/HRChart.tsx`
- [ ] Maak `hooks/useChartData.ts`

### Integration
- [ ] Integreer charts in `app/session.tsx`
- [ ] Integreer charts in `components/history/SessionDetail.tsx`
- [ ] Test met real-time data
- [ ] Test met historische data

### Polish
- [ ] Styling en theming
- [ ] Error handling
- [ ] Loading states
- [ ] Empty states

## 🚀 Volgende Stappen

1. **Implementeer stap 3.11** - Real-time Data Visualization
2. **Test de implementatie** - Gebruik deze test instructies
3. **Fix eventuele issues** - Performance, styling, bugs
4. **Documenteer** - Maak `FASE3_11_COMPLETE.md`

## 💡 Aanbeveling

Voor implementatie:
1. Kies een chart library (aanbevolen: `victory-native` voor flexibiliteit)
2. Start met een simpele HR chart
3. Voeg RR chart toe
4. Implementeer ECG chart als laatste (meest complex)
5. Test elke chart individueel voordat je integreert

## 📚 Resources

- Victory Native: https://formidable.com/open-source/victory/docs/native/
- React Native SVG: https://github.com/react-native-svg/react-native-svg
- React Native Chart Kit: https://github.com/indiespirit/react-native-chart-kit
