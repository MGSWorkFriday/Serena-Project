/**
 * Device List Component
 * Shows list of scanned Bluetooth devices
 */
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { DeviceCard } from './DeviceCard';
import type { BLEDevice } from '@/services/bluetooth/types';

interface DeviceListProps {
  devices: BLEDevice[];
  connectedDeviceId: string | null;
  connectingDeviceId: string | null;
  onDevicePress: (device: BLEDevice) => void;
  onConnect: (deviceId: string) => void;
  onDisconnect: () => void;
  refreshing?: boolean;
  onRefresh?: () => void;
}

export function DeviceList({
  devices,
  connectedDeviceId,
  connectingDeviceId,
  onDevicePress,
  onConnect,
  onDisconnect,
  refreshing = false,
  onRefresh,
}: DeviceListProps) {
  if (devices.length === 0) {
    return (
      <ThemedView style={styles.emptyContainer}>
        <ThemedText style={styles.emptyText}>Geen devices gevonden</ThemedText>
        <ThemedText style={styles.emptyHint}>
          Zorg dat je Polar H10 aan staat en dichtbij is
        </ThemedText>
      </ThemedView>
    );
  }

  return (
    <FlatList
      data={devices}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <DeviceCard
          device={item}
          isConnected={item.id === connectedDeviceId}
          isConnecting={item.id === connectingDeviceId}
          onPress={() => onDevicePress(item)}
          onConnect={() => onConnect(item.id)}
          onDisconnect={onDisconnect}
        />
      )}
      contentContainerStyle={styles.list}
      refreshControl={
        onRefresh ? (
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        ) : undefined
      }
      showsVerticalScrollIndicator={false}
    />
  );
}

const styles = StyleSheet.create({
  list: {
    padding: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    opacity: 0.7,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyHint: {
    fontSize: 14,
    opacity: 0.5,
    textAlign: 'center',
  },
});
