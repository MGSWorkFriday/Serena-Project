/**
 * Polar H10 BLE — web via Web Bluetooth API (navigator.bluetooth).
 * Used when importing from services/bluetooth on web. Falls back to stub if
 * navigator.bluetooth is missing (Safari, Firefox, or insecure context).
 *
 * Optioneel alleen voor dev: vervang de eerste regel van createService() door:
 *   const useWebBle = (typeof __DEV__ !== 'undefined' && __DEV__) && hasWebBLE;
 */
/// <reference path="./web-bluetooth.d.ts" />
import {
  POLAR_PMD_SERVICE_UUID,
  POLAR_PMD_CONTROL_UUID,
  POLAR_PMD_DATA_UUID,
  POLAR_BATTERY_SERVICE_UUID,
  POLAR_HR_SERVICE_UUID,
  HEART_RATE_CHARACTERISTIC_UUID,
  BATTERY_CHARACTERISTIC_UUID,
  START_ECG_CMD,
  STOP_STREAM_CMD,
} from './constants';
import { parsePmdEcgBytes, parseHrBytes } from './parse';
import type { BLEDevice, BluetoothState, ECGData, HeartRateData } from './types';

const hasWebBLE = typeof navigator !== 'undefined' && !!navigator?.bluetooth;

// --- Stub when Web Bluetooth is unavailable ---
class PolarServiceStub {
  async initialize(): Promise<void> {}
  async getState(): Promise<BluetoothState> {
    return 'Unsupported';
  }
  async scanForDevices(_onDeviceFound: (d: BLEDevice) => void, _timeout?: number): Promise<void> {}
  async stopScan(): Promise<void> {}
  async connect(_deviceId: string): Promise<void> {
    throw new Error('Bluetooth is not available in this browser');
  }
  async disconnect(): Promise<void> {}
  async subscribeToECG(_onData: (d: ECGData) => void): Promise<void> {
    throw new Error('Bluetooth is not available in this browser');
  }
  async subscribeToHeartRate(_onData: (d: HeartRateData) => void): Promise<void> {
    throw new Error('Bluetooth is not available in this browser');
  }
  async getBatteryLevel(): Promise<number | null> {
    return null;
  }
  isConnected(): boolean {
    return false;
  }
  getConnectedDeviceId(): string | null {
    return null;
  }
  destroy(): void {}
}

// --- Web Bluetooth implementation ---
class PolarServiceWeb {
  private deviceMap = new Map<string, BluetoothDevice>();
  private connectedDevice: BluetoothDevice | null = null;
  private ecgSequenceNumber = 0;
  private onECG: ((d: ECGData) => void) | null = null;
  private onHR: ((d: HeartRateData) => void) | null = null;

  async initialize(): Promise<void> {}

  async getState(): Promise<BluetoothState> {
    return hasWebBLE ? 'Available' : 'Unsupported';
  }

  async scanForDevices(onDeviceFound: (d: BLEDevice) => void, _timeout?: number): Promise<void> {
    if (!navigator.bluetooth) throw new Error('Web Bluetooth is not available');
    try {
      // Alleen Polar wearables: namePrefix 'Polar' + bekende modelnamen zonder prefix
      const device = await navigator.bluetooth.requestDevice({
        filters: [
          { namePrefix: 'Polar' },
          { name: 'H10' },
          { name: 'H9' },
          { name: 'OH1' },
          { name: 'OH1+' },
        ],
        optionalServices: [POLAR_PMD_SERVICE_UUID, POLAR_HR_SERVICE_UUID, POLAR_BATTERY_SERVICE_UUID],
      });
      this.deviceMap.set(device.id, device);
      // Direct verbinden na kiezen werkt op Windows vaak beter dan later via Verbinden.
      if (device.gatt) {
        try {
          await device.gatt.connect();
          this.connectedDevice = device;
        } catch {
          // Mislukt: device staat in lijst, gebruiker kan Verbinden proberen.
        }
      }
      onDeviceFound({
        id: device.id,
        name: device.name ?? null,
        rssi: null,
        isConnectable: true,
      });
    } catch (e) {
      if ((e as Error)?.name !== 'NotFoundError') throw e;
    }
  }

  async stopScan(): Promise<void> {}

  async connect(deviceId: string): Promise<void> {
    const device = this.deviceMap.get(deviceId);
    if (!device) throw new Error('Device not found. Call scan en selecteer opnieuw een device.');
    if (!device.gatt) throw new Error('Geen GATT-server op device.');
    try {
      await device.gatt.connect();
      this.connectedDevice = device;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Connection attempt failed';
      throw new Error(
        `${msg} Tip: ontkoppel de Polar in Windows (Instellingen → Bluetooth → apparaat → Verwijderen), zet de Polar even uit en aan, scan opnieuw en verbind.`
      );
    }
  }

  async disconnect(): Promise<void> {
    if (this.connectedDevice?.gatt?.connected) {
      try {
        const pmd = await this.connectedDevice.gatt!.getPrimaryService(POLAR_PMD_SERVICE_UUID);
        const ctrl = await pmd.getCharacteristic(POLAR_PMD_CONTROL_UUID);
        await ctrl.writeValueWithResponse(STOP_STREAM_CMD);
      } catch {
        // ignore if already disconnecting
      }
      this.connectedDevice.gatt.disconnect();
    }
    this.connectedDevice = null;
  }

  async subscribeToECG(onData: (data: ECGData) => void): Promise<void> {
    if (!this.connectedDevice?.gatt?.connected) throw new Error('No device connected');
    this.onECG = onData;
    console.log('[WebBLE] subscribeToECG: device connected, starting...');

    const server = this.connectedDevice.gatt!;
    const pmd = await server.getPrimaryService(POLAR_PMD_SERVICE_UUID);
    console.log('[WebBLE] Got PMD service');
    
    const ctrl = await pmd.getCharacteristic(POLAR_PMD_CONTROL_UUID);
    console.log('[WebBLE] Got control characteristic, sending START_ECG_CMD...');
    await ctrl.writeValueWithResponse(START_ECG_CMD);
    console.log('[WebBLE] START_ECG_CMD sent successfully');

    const dataChar = await pmd.getCharacteristic(POLAR_PMD_DATA_UUID);
    console.log('[WebBLE] Got data characteristic, starting notifications...');
    await dataChar.startNotifications();
    console.log('[WebBLE] Notifications started, waiting for ECG data events...');
    
    dataChar.addEventListener('characteristicvaluechanged', (ev: Event) => {
      console.log('[WebBLE] characteristicvaluechanged event received!');
      const dv = (ev.target as BluetoothRemoteGATTCharacteristic).value;
      if (!dv || !this.onECG) {
        console.log('[WebBLE] No DataView or no onECG callback');
        return;
      }
      const bytes = Array.from(new Uint8Array(dv.buffer, dv.byteOffset, dv.byteLength));
      console.log('[WebBLE] Raw bytes length:', bytes.length, 'first bytes:', bytes.slice(0, 10));
      const samples = parsePmdEcgBytes(bytes);
      console.log('[WebBLE] Parsed samples:', samples.length);
      if (samples.length) this.onECG!({ timestamp: Date.now(), samples, sequenceNumber: this.ecgSequenceNumber++ });
    });
  }

  async subscribeToHeartRate(onData: (data: HeartRateData) => void): Promise<void> {
    if (!this.connectedDevice?.gatt?.connected) throw new Error('No device connected');
    this.onHR = onData;

    const server = this.connectedDevice.gatt!;
    const hr = await server.getPrimaryService(POLAR_HR_SERVICE_UUID);
    const char = await hr.getCharacteristic(HEART_RATE_CHARACTERISTIC_UUID);
    await char.startNotifications();
    char.addEventListener('characteristicvaluechanged', (ev: Event) => {
      const dv = (ev.target as BluetoothRemoteGATTCharacteristic).value;
      if (!dv || !this.onHR) return;
      const bytes = Array.from(new Uint8Array(dv.buffer, dv.byteOffset, dv.byteLength));
      const { bpm, rrIntervals } = parseHrBytes(bytes);
      this.onHR!({ timestamp: Date.now(), bpm, rrIntervals });
    });
  }

  async getBatteryLevel(): Promise<number | null> {
    if (!this.connectedDevice?.gatt?.connected) return null;
    try {
      const s = await this.connectedDevice.gatt!.getPrimaryService(POLAR_BATTERY_SERVICE_UUID);
      const c = await s.getCharacteristic(BATTERY_CHARACTERISTIC_UUID);
      const v = await c.readValue();
      return v.getUint8(0) ?? null;
    } catch {
      return null;
    }
  }

  isConnected(): boolean {
    return !!this.connectedDevice?.gatt?.connected;
  }

  getConnectedDeviceId(): string | null {
    return this.connectedDevice?.id ?? null;
  }

  destroy(): void {
    this.disconnect();
  }
}

function createService(): PolarServiceStub | PolarServiceWeb {
  if (hasWebBLE) return new PolarServiceWeb();
  return new PolarServiceStub();
}

export const polarService = createService();
export default polarService;
export * from './types';
