# Dependency Versie Fixes Toegepast

## ✅ Opgelost

1. **expo-speech**: `~13.0.2` → `~14.0.8` (juiste versie voor Expo SDK 54)
2. **expo-av**: `~16.0.8` → `~15.0.3` (juiste versie voor Expo SDK 54)

## 📦 Installatie

Probeer nu opnieuw:

```bash
cd Mobile
npm install
```

Dit zou nu moeten werken zonder de `ETARGET` error.

## 🔍 Als er nog problemen zijn

Als `npm install` nog steeds faalt, probeer dan:

1. **Gebruik Expo CLI voor Expo packages** (aanbevolen):
   ```bash
   npx expo install expo-speech expo-av
   ```

2. **Of installeer handmatig**:
   ```bash
   npm install expo-speech@~14.0.8 expo-av@~15.0.3
   ```

3. **Dan de rest**:
   ```bash
   npm install
   ```

## ✅ Verwachte Resultaat

Na succesvolle installatie zou je moeten kunnen:
- `npx tsc --noEmit` (TypeScript check)
- `npm start` (Expo dev server)
