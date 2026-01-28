/**
 * Polar H10 BLE UUIDs and commands — shared by native and web.
 */

// Polar H10 Service UUIDs (PMD - Polar Measurement Data)
export const POLAR_PMD_SERVICE_UUID = 'fb005c80-02e7-f387-1cad-8acd2d8df0c8';
export const POLAR_PMD_CONTROL_UUID = 'fb005c81-02e7-f387-1cad-8acd2d8df0c8';
export const POLAR_PMD_DATA_UUID = 'fb005c82-02e7-f387-1cad-8acd2d8df0c8';
export const POLAR_BATTERY_SERVICE_UUID = '0000180f-0000-1000-8000-00805f9b34fb';
export const POLAR_HR_SERVICE_UUID = '0000180d-0000-1000-8000-00805f9b34fb';

// Characteristics
export const HEART_RATE_CHARACTERISTIC_UUID = '00002a37-0000-1000-8000-00805f9b34fb';
export const BATTERY_CHARACTERISTIC_UUID = '00002a19-0000-1000-8000-00805f9b34fb';

// PMD commands
export const START_ECG_CMD = new Uint8Array([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0e, 0x00]);
export const STOP_STREAM_CMD = new Uint8Array([0x03, 0x00]);
