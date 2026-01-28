/**
 * Application configuration
 */
import Constants from 'expo-constants';

const getApiBaseUrl = (): string => {
  // Check for environment variable first
  const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (envUrl) {
    return envUrl;
  }

  // Development defaults
  if (__DEV__) {
    // For iOS simulator / Android emulator, use localhost
    // For physical device, use your computer's IP address
    return 'http://localhost:8000';
  }

  // Production API URL (update when deploying)
  return 'https://api.serena.app';
};

export const config = {
  api: {
    baseUrl: getApiBaseUrl(),
    v1Prefix: process.env.EXPO_PUBLIC_API_V1_PREFIX || '/api/v1',
    timeout: 30000, // 30 seconds
  },
  bluetooth: {
    // Polar H10 service UUIDs
    polarServiceUuid: '0000180d-0000-1000-8000-00805f9b34fb',
    heartRateCharacteristicUuid: '00002a37-0000-1000-8000-00805f9b34fb',
    batteryCharacteristicUuid: '00002a19-0000-1000-8000-00805f9b34fb',
  },
  session: {
    minBufferSize: 20, // Minimum ECG samples before processing
    updateInterval: 100, // ms between signal updates
  },
  audio: {
    enabled: true,
    ttsEnabled: true,
  },
} as const;
