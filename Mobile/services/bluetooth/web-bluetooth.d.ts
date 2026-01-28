/**
 * Minimal Web Bluetooth API types for Polar H10 (Edge/Chrome).
 * Full typings: @types/web or @types/web-bluetooth
 */
interface Bluetooth {
  requestDevice(options: RequestDeviceOptions): Promise<BluetoothDevice>;
}

interface RequestDeviceOptions {
  filters?: BluetoothLEScanFilter[];
  acceptAllDevices?: boolean;
  optionalServices?: BluetoothServiceUUID[];
}

interface BluetoothLEScanFilter {
  services?: BluetoothServiceUUID[];
}

type BluetoothServiceUUID = number | string;

interface BluetoothDevice {
  id: string;
  name?: string | null;
  gatt?: BluetoothRemoteGATTServer;
}

interface BluetoothRemoteGATTServer {
  connect(): Promise<BluetoothRemoteGATTServer>;
  disconnect(): void;
  getPrimaryService(uuid: BluetoothServiceUUID): Promise<BluetoothRemoteGATTService>;
  readonly connected: boolean;
}

interface BluetoothRemoteGATTService {
  getCharacteristic(uuid: BluetoothServiceUUID): Promise<BluetoothRemoteGATTCharacteristic>;
}

interface BluetoothRemoteGATTCharacteristic extends EventTarget {
  readValue(): Promise<DataView>;
  writeValueWithResponse(data: BufferSource): Promise<void>;
  startNotifications(): Promise<BluetoothRemoteGATTCharacteristic>;
  value?: DataView;
}

interface Navigator {
  bluetooth?: Bluetooth;
}
