/**
 * Jest Setup File
 * Global test configuration and mocks
 */
import '@testing-library/jest-native/extend-expect';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock Expo modules
jest.mock('expo-constants', () => ({
  expoConfig: {
    version: '1.0.0',
    ios: { buildNumber: '1' },
    android: { versionCode: 1 },
  },
}));

jest.mock('expo-speech', () => ({
  speak: jest.fn(),
  stop: jest.fn(),
  isSpeakingAsync: jest.fn(() => Promise.resolve(false)),
}));

jest.mock('expo-av', () => ({
  Audio: {
    Sound: jest.fn(),
  },
}));

// Mock React Native BLE PLX
jest.mock('react-native-ble-plx', () => ({
  BleManager: jest.fn(() => ({
    state: jest.fn(() => Promise.resolve('PoweredOn')),
    startDeviceScan: jest.fn(),
    stopDeviceScan: jest.fn(),
    connectToDevice: jest.fn(),
    cancelDeviceConnection: jest.fn(),
    readCharacteristicForDevice: jest.fn(),
    writeCharacteristicForDevice: jest.fn(),
    monitorCharacteristicForDevice: jest.fn(),
  })),
  State: {
    Unknown: 'Unknown',
    Resetting: 'Resetting',
    Unsupported: 'Unsupported',
    Unauthorized: 'Unauthorized',
    PoweredOff: 'PoweredOff',
    PoweredOn: 'PoweredOn',
  },
}));

// Mock React Native Reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Silence console warnings in tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
};
