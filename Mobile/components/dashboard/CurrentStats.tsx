/**
 * Current Stats Component
 * Shows latest HR and RR values
 */
import { View, Text, StyleSheet } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useLatestHR, useLatestRR } from '@/hooks/useRecentSignals';
import { useBluetooth } from '@/hooks/useBluetooth';

export function CurrentStats() {
  const { deviceId, connected } = useBluetooth();
  const { bpm } = useLatestHR(deviceId || undefined);
  const { estRR } = useLatestRR(deviceId || undefined);

  if (!connected || !deviceId) {
    return (
      <ThemedView style={styles.container}>
        <ThemedText style={styles.noData}>Geen data beschikbaar</ThemedText>
        <ThemedText style={styles.hint}>Verbind een device om stats te zien</ThemedText>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle" style={styles.title}>
        Huidige Stats
      </ThemedText>
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <View style={styles.statHeader}>
            <IconSymbol name="heart.fill" size={20} color="#ef4444" />
            <ThemedText style={styles.statLabel}>Hartslag</ThemedText>
          </View>
          <ThemedText type="title" style={styles.statValue}>
            {bpm ? Math.round(bpm) : '--'}
          </ThemedText>
          <ThemedText style={styles.statUnit}>BPM</ThemedText>
        </View>

        <View style={styles.statCard}>
          <View style={styles.statHeader}>
            <IconSymbol name="lungs.fill" size={20} color="#10b981" />
            <ThemedText style={styles.statLabel}>Ademhaling</ThemedText>
          </View>
          <ThemedText type="title" style={styles.statValue}>
            {estRR ? estRR.toFixed(1) : '--'}
          </ThemedText>
          <ThemedText style={styles.statUnit}>bpm</ThemedText>
        </View>
      </View>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  title: {
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    alignItems: 'center',
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 12,
    opacity: 0.7,
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statUnit: {
    fontSize: 12,
    opacity: 0.6,
  },
  noData: {
    textAlign: 'center',
    opacity: 0.6,
    marginBottom: 4,
  },
  hint: {
    textAlign: 'center',
    fontSize: 12,
    opacity: 0.5,
  },
});
