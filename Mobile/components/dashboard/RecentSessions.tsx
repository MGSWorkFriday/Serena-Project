/**
 * Recent Sessions Component
 * Shows list of recent sessions
 */
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useSessions } from '@/hooks/useSessions';
import { useBluetooth } from '@/hooks/useBluetooth';
import { format } from 'date-fns';
import { router } from 'expo-router';

export function RecentSessions() {
  const { deviceId } = useBluetooth();
  const { data: sessions, isLoading } = useSessions(deviceId || undefined);

  const recentSessions = sessions?.slice(0, 5) || [];

  const formatDuration = (startedAt: string, endedAt?: string) => {
    if (!endedAt) return 'Lopend...';
    const start = new Date(startedAt);
    const end = new Date(endedAt);
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ${seconds % 60}s`;
  };

  if (isLoading) {
    return (
      <ThemedView style={styles.container}>
        <ThemedText type="subtitle">Recent Sessions</ThemedText>
        <ThemedText>Laden...</ThemedText>
      </ThemedView>
    );
  }

  if (recentSessions.length === 0) {
    return (
      <ThemedView style={styles.container}>
        <ThemedText type="subtitle">Recent Sessions</ThemedText>
        <ThemedText style={styles.emptyText}>Nog geen sessies</ThemedText>
        <TouchableOpacity
          onPress={() => router.push('/(tabs)/history')}
          style={styles.viewAllButton}>
          <ThemedText style={styles.viewAllText}>Bekijk geschiedenis →</ThemedText>
        </TouchableOpacity>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <View style={styles.header}>
        <ThemedText type="subtitle">Recent Sessions</ThemedText>
        <TouchableOpacity onPress={() => router.push('/(tabs)/history')}>
          <ThemedText style={styles.viewAllText}>Alles →</ThemedText>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
        {recentSessions.map((session) => (
          <TouchableOpacity
            key={session.session_id}
            style={styles.sessionItem}
            onPress={() => {
              // TODO: Navigate to session detail
              router.push('/(tabs)/history');
            }}>
            <View style={styles.sessionHeader}>
              <ThemedText type="defaultSemiBold">
                {format(new Date(session.started_at), 'dd MMM HH:mm')}
              </ThemedText>
              <View
                style={[
                  styles.statusBadge,
                  session.status === 'active' && styles.statusActive,
                  session.status === 'completed' && styles.statusCompleted,
                ]}>
                <ThemedText style={styles.statusText}>{session.status}</ThemedText>
              </View>
            </View>

            {session.technique_name && (
              <ThemedText style={styles.technique}>{session.technique_name}</ThemedText>
            )}

            <View style={styles.sessionFooter}>
              <ThemedText style={styles.duration}>
                {formatDuration(session.started_at, session.ended_at)}
              </ThemedText>
              {session.target_rr && (
                <ThemedText style={styles.targetRR}>Doel: {session.target_rr} bpm</ThemedText>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  viewAllText: {
    fontSize: 14,
    opacity: 0.7,
  },
  viewAllButton: {
    marginTop: 8,
  },
  list: {
    maxHeight: 300,
  },
  sessionItem: {
    padding: 12,
    marginBottom: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
  },
  sessionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.2)',
  },
  statusActive: {
    backgroundColor: '#10b981',
  },
  statusCompleted: {
    backgroundColor: '#3b82f6',
  },
  statusText: {
    fontSize: 10,
    color: '#fff',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  technique: {
    fontSize: 14,
    opacity: 0.8,
    marginBottom: 4,
  },
  sessionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  duration: {
    fontSize: 12,
    opacity: 0.6,
  },
  targetRR: {
    fontSize: 12,
    opacity: 0.6,
  },
  emptyText: {
    opacity: 0.6,
    marginTop: 8,
  },
});
