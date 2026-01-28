# Test Instructions voor Mobile App

## 1. Installeer Dependencies

```bash
cd Mobile
npm install
```

Dit installeert alle benodigde packages:
- `@tanstack/react-query`
- `axios`
- `react-native-ble-plx`
- `@react-native-async-storage/async-storage`
- `expo-av`, `expo-speech`
- `date-fns`
- `react-native-svg`

## 2. TypeScript Check

```bash
npx tsc --noEmit
```

Na installatie van dependencies zouden de TypeScript errors opgelost moeten zijn.

## 3. Expo Start

```bash
npm start
# Of
npx expo start
```

## 4. Test op Device/Simulator

- **iOS**: `npm run ios` of druk `i` in Expo CLI
- **Android**: `npm run android` of druk `a` in Expo CLI
- **Web**: `npm run web` of druk `w` in Expo CLI

## Bekende Issues (Opgelost)

✅ Base64 encoding/decoding - Nu React Native compatible
✅ TypeScript type errors - Types toegevoegd
✅ Constant name fix - `POLAR_SERVICE_UUID` → `POLAR_HR_SERVICE_UUID`
✅ Uint8Array to base64 - Helper functie toegevoegd

## Nog Te Testen

- [ ] Bluetooth permissions op iOS/Android
- [ ] Polar H10 device connectie
- [ ] ECG data parsing
- [ ] API client connectie met backend
- [ ] Real-time SSE streaming
- [ ] Navigation tussen screens

## Troubleshooting

### "Cannot find module" errors
- Run `npm install` opnieuw
- Check `node_modules` folder bestaat
- Verwijder `node_modules` en `package-lock.json`, run `npm install` opnieuw

### TypeScript errors
- Check of alle dependencies geïnstalleerd zijn
- Run `npx tsc --noEmit` voor details

### Bluetooth errors
- Check permissions in `app.json`
- Test op fysiek device (niet simulator voor BLE)
- Check Bluetooth staat aan op device
