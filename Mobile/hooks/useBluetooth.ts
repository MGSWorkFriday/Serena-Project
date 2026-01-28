/**
 * React hook for Bluetooth state management
 */
import { useState, useEffect, useCallback } from 'react';
import { polarService } from '@/services/bluetooth';
import type { BLEDevice, BluetoothState, ECGData, HeartRateData } from '@/services/bluetooth/types';

export interface UseBluetoothReturn {
  state: BluetoothState;
  enabled: boolean;
  scanning: boolean;
  connected: boolean;
  deviceId: string | null;
  devices: BLEDevice[];
  error: string | null;
  initialize: () => Promise<void>;
  scan: (timeout?: number) => Promise<void>;
  stopScan: () => Promise<void>;
  connect: (deviceId: string) => Promise<void>;
  disconnect: () => Promise<void>;
  subscribeECG: (onData: (data: ECGData) => void) => Promise<void>;
  subscribeHeartRate: (onData: (data: HeartRateData) => void) => Promise<void>;
  getBatteryLevel: () => Promise<number | null>;
}

export function useBluetooth(): UseBluetoothReturn {
  const [state, setState] = useState<BluetoothState>('Unknown');
  const [enabled, setEnabled] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [connected, setConnected] = useState(false);
  const [deviceId, setDeviceId] = useState<string | null>(null);
  const [devices, setDevices] = useState<BLEDevice[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Initialize Bluetooth
  const initialize = useCallback(async () => {
    try {
      setError(null);
      await polarService.initialize();
      const currentState = await polarService.getState();
      setState(currentState);
      setEnabled(currentState === 'PoweredOn' || currentState === 'Available');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initialize Bluetooth';
      setError(errorMessage);
      console.error('[useBluetooth] Initialize error:', err);
    }
  }, []);

  // Scan for devices
  const scan = useCallback(async (timeout = 10000) => {
    try {
      setError(null);
      setScanning(true);
      setDevices([]);

      const foundDevices: BLEDevice[] = [];
      const deviceMap = new Map<string, BLEDevice>();

      await polarService.scanForDevices((device) => {
        if (!deviceMap.has(device.id)) {
          deviceMap.set(device.id, device);
          foundDevices.push(device);
          setDevices([...foundDevices]);
        }
      }, timeout);

      setScanning(false);
    } catch (err) {
      setScanning(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to scan for devices';
      setError(errorMessage);
      console.error('[useBluetooth] Scan error:', err);
    }
  }, []);

  // Stop scan
  const stopScan = useCallback(async () => {
    try {
      await polarService.stopScan();
      setScanning(false);
    } catch (err) {
      console.error('[useBluetooth] Stop scan error:', err);
    }
  }, []);

  // Connect to device
  const connect = useCallback(async (deviceId: string) => {
    try {
      setError(null);
      await polarService.connect(deviceId);
      setConnected(true);
      setDeviceId(deviceId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to device';
      setError(errorMessage);
      setConnected(false);
      setDeviceId(null);
      console.error('[useBluetooth] Connect error:', err);
      throw err;
    }
  }, []);

  // Disconnect
  const disconnect = useCallback(async () => {
    try {
      await polarService.disconnect();
      setConnected(false);
      setDeviceId(null);
    } catch (err) {
      console.error('[useBluetooth] Disconnect error:', err);
    }
  }, []);

  // Subscribe to ECG
  const subscribeECG = useCallback(async (onData: (data: ECGData) => void) => {
    try {
      await polarService.subscribeToECG(onData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to subscribe to ECG';
      setError(errorMessage);
      console.error('[useBluetooth] Subscribe ECG error:', err);
      throw err;
    }
  }, []);

  // Subscribe to Heart Rate
  const subscribeHeartRate = useCallback(async (onData: (data: HeartRateData) => void) => {
    try {
      await polarService.subscribeToHeartRate(onData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to subscribe to Heart Rate';
      setError(errorMessage);
      console.error('[useBluetooth] Subscribe HR error:', err);
      throw err;
    }
  }, []);

  // Get battery level
  const getBatteryLevel = useCallback(async () => {
    try {
      return await polarService.getBatteryLevel();
    } catch (err) {
      console.error('[useBluetooth] Get battery level error:', err);
      return null;
    }
  }, []);

  // Monitor Bluetooth state
  useEffect(() => {
    let mounted = true;

    const checkState = async () => {
      try {
        const currentState = await polarService.getState();
        if (mounted) {
          setState(currentState);
          setEnabled(currentState === 'PoweredOn' || currentState === 'Available');
          setConnected(polarService.isConnected());
          setDeviceId(polarService.getConnectedDeviceId());
        }
      } catch (err) {
        console.error('[useBluetooth] State check error:', err);
      }
    };

    // Initial check
    checkState();

    // Check periodically
    const interval = setInterval(checkState, 2000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return {
    state,
    enabled,
    scanning,
    connected,
    deviceId,
    devices,
    error,
    initialize,
    scan,
    stopScan,
    connect,
    disconnect,
    subscribeECG,
    subscribeHeartRate,
    getBatteryLevel,
  };
}
