/**
 * Device Management Screen
 * Bluetooth device connection and management
 */
import { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { DeviceList } from '@/components/device/DeviceList';
import { useBluetooth } from '@/hooks/useBluetooth';
import { useDevice, useUpdateDevice, useCreateDevice } from '@/hooks/useDevices';
import { router } from 'expo-router';
import type { BLEDevice } from '@/services/bluetooth/types';

export default function DeviceScreen() {
  const {
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
    getBatteryLevel,
  } = useBluetooth();

  const { data: deviceData } = useDevice(deviceId || null);
  const updateDeviceMutation = useUpdateDevice();
  const createDeviceMutation = useCreateDevice();

  const [connectingDeviceId, setConnectingDeviceId] = useState<string | null>(null);
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);

  // Initialize Bluetooth on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Get battery level for connected device
  useEffect(() => {
    if (connected && deviceId) {
      getBatteryLevel().then(setBatteryLevel);
      // Refresh battery level every 30 seconds
      const interval = setInterval(() => {
        getBatteryLevel().then(setBatteryLevel);
      }, 30000);
      return () => clearInterval(interval);
    } else {
      setBatteryLevel(null);
    }
  }, [connected, deviceId, getBatteryLevel]);

  const handleScan = async () => {
    if (!enabled) {
      Alert.alert('Bluetooth uit', 'Schakel Bluetooth in of gebruik een browser met Web Bluetooth (bijv. Edge, Chrome) om devices te scannen.');
      return;
    }

    if (scanning) {
      await stopScan();
    } else {
      await scan(15000); // 15 second scan
    }
  };

  const handleConnect = async (targetDeviceId: string) => {
    if (connected && deviceId === targetDeviceId) {
      return; // Already connected
    }

    if (connected && deviceId !== targetDeviceId) {
      Alert.alert(
        'Al verbonden',
        'Je bent al verbonden met een ander device. Verbreek eerst de verbinding.',
        [{ text: 'OK' }]
      );
      return;
    }

    try {
      setConnectingDeviceId(targetDeviceId);
      await connect(targetDeviceId);

      // Create or update device in backend
      try {
        const deviceName = devices.find((d) => d.id === targetDeviceId)?.name;
        
        // Try to update first (device might exist)
        try {
          await updateDeviceMutation.mutateAsync({
            deviceId: targetDeviceId,
            data: {
              name: deviceName || undefined,
              metadata: {
                last_seen: new Date().toISOString(),
              },
            },
          });
        } catch (updateErr: any) {
          // If update fails (device doesn't exist), create it
          if (updateErr?.response?.status === 404 || updateErr?.message?.includes('not found')) {
            await createDeviceMutation.mutateAsync({
              device_id: targetDeviceId,
              name: deviceName || undefined,
              type: 'Polar H10',
              metadata: {
                connected_at: new Date().toISOString(),
              },
            });
          } else {
            throw updateErr;
          }
        }
      } catch (err) {
        console.error('Failed to sync device with backend:', err);
        // Non-critical error, continue
      }

      Alert.alert('Succesvol verbonden', 'Device is verbonden en klaar voor gebruik');
    } catch (err) {
      Alert.alert('Verbindingsfout', err instanceof Error ? err.message : 'Kon niet verbinden');
    } finally {
      setConnectingDeviceId(null);
    }
  };

  const handleDisconnect = async () => {
    Alert.alert(
      'Verbinding verbreken',
      'Weet je zeker dat je de verbinding wilt verbreken?',
      [
        { text: 'Annuleren', style: 'cancel' },
        {
          text: 'Verbreken',
          style: 'destructive',
          onPress: async () => {
            try {
              await disconnect();
              Alert.alert('Verbinding verbroken', 'Device is losgekoppeld');
            } catch (err) {
              Alert.alert('Fout', 'Kon verbinding niet verbreken');
            }
          },
        },
      ]
    );
  };

  const handleDevicePress = (device: BLEDevice) => {
    if (connected && deviceId === device.id) {
      // Show device info
      Alert.alert(
        device.name || 'Device',
        `ID: ${device.id}\nRSSI: ${device.rssi ?? 'Onbekend'} dBm\nBattery: ${batteryLevel !== null ? `${batteryLevel}%` : 'Onbekend'}`,
        [{ text: 'OK' }]
      );
    }
  };

  const getStatusText = () => {
    if (!enabled || (state !== 'PoweredOn' && state !== 'Available')) return 'Bluetooth uit';
    if (state === 'Available' && !connected && !scanning) return 'Klik Scan om een Polar te kiezen (browser)';
    if (connected) return `Verbonden met ${deviceData?.name || deviceId || 'device'}`;
    if (scanning) return 'Scannen naar devices...';
    return 'Niet verbonden';
  };

  const getStatusColor = () => {
    if (!enabled || (state !== 'PoweredOn' && state !== 'Available')) return '#ef4444';
    if (state === 'Available' && !connected && !scanning) return '#f59e0b';
    if (connected) return '#10b981';
    if (scanning) return '#3b82f6';
    return '#f59e0b';
  };

  return (
    <ThemedView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <IconSymbol name="chevron.left" size={24} color="#fff" />
        </TouchableOpacity>
        <ThemedText type="title" style={styles.title}>
          Device Beheer
        </ThemedText>
        <View style={styles.placeholder} />
      </View>

      {/* Status Card */}
      <View style={styles.statusCard}>
        <View style={styles.statusRow}>
          <IconSymbol
            name="antenna.radiowaves.left.and.right"
            size={24}
            color={getStatusColor()}
          />
          <View style={styles.statusText}>
            <ThemedText type="defaultSemiBold">Status</ThemedText>
            <ThemedText style={{ color: getStatusColor() }}>{getStatusText()}</ThemedText>
          </View>
        </View>

        {connected && deviceId && (
          <View style={styles.deviceInfo}>
            <ThemedText style={styles.deviceId}>Device ID: {deviceId}</ThemedText>
            {batteryLevel !== null && (
              <ThemedText style={styles.battery}>
                Battery: {batteryLevel}%
              </ThemedText>
            )}
            {deviceData?.last_seen && (
              <ThemedText style={styles.lastSeen}>
                Laatst gezien: {new Date(deviceData.last_seen).toLocaleString()}
              </ThemedText>
            )}
          </View>
        )}

        {error && (
          <ThemedText style={[styles.error, { color: '#ef4444' }]}>{error}</ThemedText>
        )}
      </View>

      {/* Scan Button */}
      <View style={styles.actions}>
        <TouchableOpacity
          onPress={handleScan}
          disabled={!enabled || connectingDeviceId !== null}
          style={[
            styles.scanButton,
            (!enabled || connectingDeviceId !== null) && styles.scanButtonDisabled,
            scanning && styles.scanButtonActive,
          ]}>
          {scanning ? (
            <>
              <ActivityIndicator size="small" color="#fff" />
              <ThemedText style={styles.scanButtonText}>Stoppen...</ThemedText>
            </>
          ) : (
            <>
              <IconSymbol name="magnifyingglass" size={20} color="#fff" />
              <ThemedText style={styles.scanButtonText}>Scan naar Polar</ThemedText>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Device List */}
      <DeviceList
        devices={devices}
        connectedDeviceId={deviceId}
        connectingDeviceId={connectingDeviceId}
        onDevicePress={handleDevicePress}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
        refreshing={scanning}
        onRefresh={handleScan}
      />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    paddingBottom: 12,
  },
  backButton: {
    padding: 8,
  },
  title: {
    flex: 1,
    textAlign: 'center',
    fontSize: 24,
  },
  placeholder: {
    width: 40,
  },
  statusCard: {
    margin: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  statusText: {
    flex: 1,
  },
  deviceInfo: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  deviceId: {
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 4,
  },
  battery: {
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 4,
  },
  lastSeen: {
    fontSize: 11,
    opacity: 0.6,
  },
  error: {
    fontSize: 12,
    marginTop: 8,
  },
  actions: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  scanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#3b82f6',
  },
  scanButtonActive: {
    backgroundColor: '#ef4444',
  },
  scanButtonDisabled: {
    backgroundColor: '#6b7280',
    opacity: 0.6,
  },
  scanButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
