/**
 * Bluetooth Low Energy types
 */

export interface BLEDevice {
  id: string;
  name: string | null;
  rssi: number | null;
  isConnectable: boolean | null;
}

export interface ConnectedDevice extends BLEDevice {
  connected: boolean;
  services: BLEService[];
}

export interface BLEService {
  uuid: string;
  characteristics: BLECharacteristic[];
}

export interface BLECharacteristic {
  uuid: string;
  properties: string[];
}

export interface ECGData {
  timestamp: number; // milliseconds
  samples: number[]; // ECG sample values
  sequenceNumber?: number;
}

export interface HeartRateData {
  timestamp: number; // milliseconds
  bpm: number;
  rrIntervals?: number[]; // RR intervals in milliseconds
}

export type BluetoothState = 'Unknown' | 'Resetting' | 'Unsupported' | 'Unauthorized' | 'PoweredOff' | 'PoweredOn' | 'Available';

export interface BluetoothStatus {
  state: BluetoothState;
  enabled: boolean;
  scanning: boolean;
  connected: boolean;
  deviceId: string | null;
}
