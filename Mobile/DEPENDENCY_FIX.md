# Dependency Versie Fixes

## Probleem
`expo-speech@~13.0.2` bestaat niet voor Expo SDK 54.

## Oplossing
Voor Expo SDK 54 moet `expo-speech` versie `~14.0.8` zijn.

## Aangepast
- ✅ `expo-speech`: `~13.0.2` → `~14.0.8`
- ✅ `expo-av`: `~16.0.8` → `~15.0.3` (ook gecorrigeerd voor SDK 54)

## Installatie
Na deze fix zou `npm install` moeten werken:

```bash
cd Mobile
npm install
```

## Alternatief: Expo CLI
Voor Expo packages is het aanbevolen om `expo install` te gebruiken:

```bash
npx expo install expo-speech expo-av
```

Dit installeert automatisch de juiste versies voor je Expo SDK versie.
