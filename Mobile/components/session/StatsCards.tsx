/**
 * Stats Cards Component
 * Shows Heart Rate, Actual RR, and Target RR
 */
import { View, Text, StyleSheet } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';

interface StatsCardsProps {
  heartRate?: number;
  actualRR?: number;
  targetRR?: number;
}

export function StatsCards({ heartRate, actualRR, targetRR }: StatsCardsProps) {
  return (
    <View style={styles.container}>
      <ThemedView style={styles.card}>
        <View style={styles.cardHeader}>
          <IconSymbol name="heart.fill" size={24} color="#ef4444" />
          <ThemedText style={styles.cardLabel}>Hartslag</ThemedText>
        </View>
        <ThemedText type="title" style={styles.cardValue}>
          {heartRate ? Math.round(heartRate) : '--'}
        </ThemedText>
        <ThemedText style={styles.cardUnit}>BPM</ThemedText>
      </ThemedView>

      <ThemedView style={styles.card}>
        <View style={styles.cardHeader}>
          <IconSymbol name="lungs.fill" size={24} color="#10b981" />
          <ThemedText style={styles.cardLabel}>Ademhaling</ThemedText>
        </View>
        <ThemedText type="title" style={styles.cardValue}>
          {actualRR ? actualRR.toFixed(1) : '--'}
        </ThemedText>
        <ThemedText style={styles.cardUnit}>bpm</ThemedText>
      </ThemedView>

      {targetRR && targetRR > 0 && (
        <ThemedView style={styles.card}>
          <View style={styles.cardHeader}>
            <IconSymbol name="target" size={24} color="#3b82f6" />
            <ThemedText style={styles.cardLabel}>Doel</ThemedText>
          </View>
          <ThemedText type="title" style={styles.cardValue}>
            {targetRR.toFixed(1)}
          </ThemedText>
          <ThemedText style={styles.cardUnit}>bpm</ThemedText>
        </ThemedView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  card: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    alignItems: 'center',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  cardLabel: {
    fontSize: 12,
    opacity: 0.7,
  },
  cardValue: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cardUnit: {
    fontSize: 11,
    opacity: 0.6,
  },
});
