/**
 * Device Card Component
 * Displays a single Bluetooth device with connection options
 */
import { View, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import type { BLEDevice } from '@/services/bluetooth/types';

interface DeviceCardProps {
  device: BLEDevice;
  isConnected: boolean;
  isConnecting: boolean;
  onPress: () => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function DeviceCard({
  device,
  isConnected,
  isConnecting,
  onPress,
  onConnect,
  onDisconnect,
}: DeviceCardProps) {
  const getSignalStrength = (rssi: number | null): string => {
    if (rssi === null) return 'Onbekend';
    if (rssi >= -50) return 'Uitstekend';
    if (rssi >= -70) return 'Goed';
    if (rssi >= -85) return 'Redelijk';
    return 'Zwak';
  };

  const getSignalColor = (rssi: number | null): string => {
    if (rssi === null) return '#6b7280';
    if (rssi >= -50) return '#10b981';
    if (rssi >= -70) return '#3b82f6';
    if (rssi >= -85) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <ThemedView
        style={[
          styles.card,
          isConnected && styles.cardConnected,
          { borderLeftColor: isConnected ? '#10b981' : getSignalColor(device.rssi) },
        ]}>
        <View style={styles.header}>
          <View style={styles.deviceInfo}>
            <IconSymbol
              name={isConnected ? 'antenna.radiowaves.left.and.right' : 'antenna.radiowaves.left.and.right'}
              size={24}
              color={isConnected ? '#10b981' : '#6b7280'}
            />
            <View style={styles.deviceDetails}>
              <ThemedText type="defaultSemiBold" style={styles.deviceName}>
                {device.name || 'Onbekend Device'}
              </ThemedText>
              <ThemedText style={styles.deviceId}>{device.id}</ThemedText>
            </View>
          </View>
          {isConnecting && <ActivityIndicator size="small" color="#3b82f6" />}
          {isConnected && (
            <View style={styles.connectedBadge}>
              <ThemedText style={styles.connectedText}>Verbonden</ThemedText>
            </View>
          )}
        </View>

        <View style={styles.footer}>
          <View style={styles.signalInfo}>
            <IconSymbol name="antenna.radiowaves.left.and.right" size={16} color={getSignalColor(device.rssi)} />
            <ThemedText style={[styles.signalText, { color: getSignalColor(device.rssi) }]}>
              {getSignalStrength(device.rssi)}
              {device.rssi !== null && ` (${device.rssi} dBm)`}
            </ThemedText>
          </View>

          {isConnected ? (
            <TouchableOpacity
              onPress={(e) => {
                e.stopPropagation();
                onDisconnect?.();
              }}
              style={styles.disconnectButton}>
              <IconSymbol name="xmark.circle.fill" size={20} color="#ef4444" />
              <ThemedText style={styles.disconnectText}>Verbinding verbreken</ThemedText>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              onPress={(e) => {
                e.stopPropagation();
                onConnect?.();
              }}
              style={styles.connectButton}
              disabled={isConnecting}>
              <IconSymbol name="link" size={20} color="#fff" />
              <ThemedText style={styles.connectText}>Verbinden</ThemedText>
            </TouchableOpacity>
          )}
        </View>
      </ThemedView>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.2)',
  },
  cardConnected: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  deviceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  deviceDetails: {
    flex: 1,
  },
  deviceName: {
    fontSize: 16,
    marginBottom: 4,
  },
  deviceId: {
    fontSize: 12,
    opacity: 0.7,
  },
  connectedBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: '#10b981',
  },
  connectedText: {
    fontSize: 11,
    color: '#fff',
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  signalInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  signalText: {
    fontSize: 12,
    fontWeight: '500',
  },
  connectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#3b82f6',
  },
  connectText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  disconnectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  disconnectText: {
    color: '#ef4444',
    fontSize: 13,
    fontWeight: '600',
  },
});
