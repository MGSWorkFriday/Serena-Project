/**
 * Polar H10 BLE — native (iOS/Android) via react-native-ble-plx.
 * Used when importing from services/bluetooth on native; index.web.ts is used on web.
 */
import { BleManager, Device, Characteristic } from 'react-native-ble-plx';
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
import { isPolarDevice } from './polarFilter';
import { parsePmdEcgBytes, parseHrBytes } from './parse';
import type { ECGData, HeartRateData, BLEDevice, BluetoothState } from './types';

class PolarServiceNative {
  private manager: BleManager;
  private connectedDevice: Device | null = null;
  private ecgSubscription: { remove: () => void } | null = null;
  private hrSubscription: { remove: () => void } | null = null;
  private onECGDataCallback: ((data: ECGData) => void) | null = null;
  private onHRDataCallback: ((data: HeartRateData) => void) | null = null;
  private ecgSequenceNumber = 0;

  constructor() {
    this.manager = new BleManager();
  }

  async initialize(): Promise<void> {
    try {
      const state = await this.manager.state();
      if (state === 'PoweredOn') return;
      return new Promise<void>((resolve, reject) => {
        const sub = this.manager.onStateChange((s: string) => {
          if (s === 'PoweredOn') {
            sub.remove();
            resolve();
          } else if (s === 'PoweredOff' || s === 'Unauthorized') {
            sub.remove();
            reject(new Error(`Bluetooth is ${s}`));
          }
        });
      });
    } catch (e) {
      throw new Error(`Failed to initialize Bluetooth: ${e}`);
    }
  }

  async getState(): Promise<BluetoothState> {
    return (await this.manager.state()) as BluetoothState;
  }

  async scanForDevices(onDeviceFound: (d: BLEDevice) => void, timeout = 10000): Promise<void> {
    await this.manager.stopDeviceScan();
    this.manager.startDeviceScan(
      [POLAR_PMD_SERVICE_UUID, POLAR_HR_SERVICE_UUID],
      { allowDuplicates: false },
      (err: unknown, device: Device | null) => {
        if (err) {
          console.error('[Polar] Scan error:', err);
          return;
        }
        if (device) {
          const rawName = device.name || device.localName || null;
          if (!isPolarDevice(rawName)) return;
          onDeviceFound({
            id: device.id,
            name: device.name || device.localName || 'Unknown Device',
            rssi: device.rssi,
            isConnectable: device.isConnectable,
          });
        }
      }
    );
    setTimeout(() => this.manager.stopDeviceScan(), timeout);
  }

  async stopScan(): Promise<void> {
    await this.manager.stopDeviceScan();
  }

  async connect(deviceId: string): Promise<void> {
    if (this.connectedDevice?.id === deviceId) return;
    if (this.connectedDevice) await this.disconnect();

    const device = await this.manager.connectToDevice(deviceId);
    await device.discoverAllServicesAndCharacteristics();
    this.connectedDevice = device;

    device.onDisconnected(() => {
      this.connectedDevice = null;
      this.ecgSubscription = null;
      this.hrSubscription = null;
    });
  }

  async disconnect(): Promise<void> {
    if (this.connectedDevice && this.ecgSubscription) {
      try {
        await this.connectedDevice.writeCharacteristicWithResponseForService(
          POLAR_PMD_SERVICE_UUID,
          POLAR_PMD_CONTROL_UUID,
          this.uint8ArrayToBase64(STOP_STREAM_CMD)
        );
      } catch (e) {
        console.error('[Polar] Error stopping stream:', e);
      }
    }
    this.ecgSubscription?.remove();
    this.ecgSubscription = null;
    this.hrSubscription?.remove();
    this.hrSubscription = null;
    if (this.connectedDevice) {
      await this.connectedDevice.cancelConnection();
      this.connectedDevice = null;
    }
  }

  async subscribeToECG(onData: (data: ECGData) => void): Promise<void> {
    if (!this.connectedDevice) throw new Error('No device connected');
    this.onECGDataCallback = onData;

    await this.connectedDevice.writeCharacteristicWithResponseForService(
      POLAR_PMD_SERVICE_UUID,
      POLAR_PMD_CONTROL_UUID,
      this.uint8ArrayToBase64(START_ECG_CMD)
    );

    const dataChar = await this.connectedDevice.readCharacteristicForService(
      POLAR_PMD_SERVICE_UUID,
      POLAR_PMD_DATA_UUID
    );

    this.ecgSubscription = dataChar.monitor((err: unknown, c: Characteristic | null) => {
      if (err || !c?.value) return;
      const bytes = this.base64ToBytes(c.value);
      const samples = parsePmdEcgBytes(bytes);
      if (samples.length && this.onECGDataCallback) {
        this.onECGDataCallback({ timestamp: Date.now(), samples, sequenceNumber: this.ecgSequenceNumber++ });
      }
    });
  }

  async subscribeToHeartRate(onData: (data: HeartRateData) => void): Promise<void> {
    if (!this.connectedDevice) throw new Error('No device connected');
    this.onHRDataCallback = onData;

    const c = await this.connectedDevice.readCharacteristicForService(
      POLAR_HR_SERVICE_UUID,
      HEART_RATE_CHARACTERISTIC_UUID
    );

    this.hrSubscription = c.monitor((err: unknown, ch: Characteristic | null) => {
      if (err || !ch?.value) return;
      const { bpm, rrIntervals } = parseHrBytes(this.base64ToBytes(ch.value));
      this.onHRDataCallback?.({ timestamp: Date.now(), bpm, rrIntervals });
    });
  }

  async getBatteryLevel(): Promise<number | null> {
    if (!this.connectedDevice) return null;
    try {
      const c = await this.connectedDevice.readCharacteristicForService(
        POLAR_BATTERY_SERVICE_UUID,
        BATTERY_CHARACTERISTIC_UUID
      );
      if (c?.value) return this.base64ToBytes(c.value)[0] ?? null;
    } catch {
      // ignore
    }
    return null;
  }

  isConnected(): boolean {
    return this.connectedDevice != null;
  }

  getConnectedDeviceId(): string | null {
    return this.connectedDevice?.id ?? null;
  }

  destroy(): void {
    this.disconnect();
    this.manager.destroy();
  }

  private base64ToBytes(base64: string): number[] {
    try {
      if (typeof Buffer !== 'undefined') return Array.from(Buffer.from(base64, 'base64'));
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
      const bytes: number[] = [];
      let i = 0;
      base64 = base64.replace(/[^A-Za-z0-9+/=]/g, '');
      while (i < base64.length) {
        const enc1 = chars.indexOf(base64[i++]);
        const enc2 = chars.indexOf(base64[i++]);
        const enc3 = chars.indexOf(base64[i++]);
        const enc4 = chars.indexOf(base64[i++]);
        const b = (enc1 << 18) | (enc2 << 12) | (enc3 << 6) | enc4;
        bytes.push((b >> 16) & 255);
        if (enc3 !== 64) bytes.push((b >> 8) & 255);
        if (enc4 !== 64) bytes.push(b & 255);
      }
      return bytes;
    } catch {
      return [];
    }
  }

  private uint8ArrayToBase64(arr: Uint8Array): string {
    try {
      if (typeof Buffer !== 'undefined') return Buffer.from(arr).toString('base64');
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
      let out = '';
      let i = 0;
      while (i < arr.length) {
        const a = arr[i++];
        const b = i < arr.length ? arr[i++] : 0;
        const c = i < arr.length ? arr[i++] : 0;
        const n = (a << 16) | (b << 8) | c;
        out += chars[(n >> 18) & 63] + chars[(n >> 12) & 63] + (i - 2 < arr.length ? chars[(n >> 6) & 63] : '=') + (i - 1 < arr.length ? chars[n & 63] : '=');
      }
      return out;
    } catch {
      return '';
    }
  }
}

export const polarService = new PolarServiceNative();
export default polarService;
