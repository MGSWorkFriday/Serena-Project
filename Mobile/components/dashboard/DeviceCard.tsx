/**
 * Device Status Card Component
 * Shows Bluetooth device connection status
 */
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useBluetooth } from '@/hooks/useBluetooth';
import { useDevice } from '@/hooks/useDevices';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { router } from 'expo-router';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export function DeviceCard() {
  const colorScheme = useColorScheme();
  const { connected, deviceId, enabled, state, error } = useBluetooth();
  const { data: device, isLoading: deviceLoading } = useDevice(deviceId || null);

  const handlePress = () => {
    router.push('/device');
  };

  const getStatusColor = () => {
    if (!enabled || (state !== 'PoweredOn' && state !== 'Available')) return '#ef4444'; // Red
    if (state === 'Available' && !connected) return '#f59e0b'; // Orange: web, kies device
    if (connected) return '#10b981'; // Green
    return '#f59e0b'; // Orange
  };

  const getStatusText = () => {
    if (!enabled || (state !== 'PoweredOn' && state !== 'Available')) return 'Bluetooth uit';
    if (state === 'Available' && !connected) return 'Klik Beheer device om Polar te kiezen';
    if (connected) return device?.name || deviceId || 'Verbonden';
    return 'Niet verbonden';
  };

  return (
    <TouchableOpacity onPress={handlePress} activeOpacity={0.7}>
      <ThemedView style={[styles.card, { borderLeftColor: getStatusColor() }]}>
        <View style={styles.header}>
          <View style={styles.statusRow}>
            <IconSymbol name="antenna.radiowaves.left.and.right" size={24} color={getStatusColor()} />
            <View style={styles.statusText}>
              <ThemedText type="defaultSemiBold">Device Status</ThemedText>
              <ThemedText type="subtitle" style={{ color: getStatusColor() }}>
                {getStatusText()}
              </ThemedText>
            </View>
          </View>
          {deviceLoading && <ActivityIndicator size="small" />}
        </View>

        {connected && deviceId && (
          <View style={styles.deviceInfo}>
            <ThemedText style={styles.deviceId}>ID: {deviceId}</ThemedText>
            {device?.last_seen && (
              <ThemedText style={styles.lastSeen}>
                Laatst gezien: {new Date(device.last_seen).toLocaleTimeString()}
              </ThemedText>
            )}
          </View>
        )}

        {error && (
          <ThemedText style={[styles.error, { color: Colors[colorScheme ?? 'light'].tint }]}>
            {error}
          </ThemedText>
        )}

        <View style={styles.footer}>
          <ThemedText style={styles.link}>Beheer device →</ThemedText>
        </View>
      </ThemedView>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statusText: {
    flex: 1,
  },
  deviceInfo: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  deviceId: {
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
  footer: {
    marginTop: 8,
    alignItems: 'flex-end',
  },
  link: {
    fontSize: 12,
    opacity: 0.7,
  },
});
