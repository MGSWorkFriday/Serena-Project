/**
 * Session Card Component
 * Displays a single session in the history list
 */
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import type { Session } from '@/services/api/types';

interface SessionCardProps {
  session: Session;
  onPress: () => void;
}

export function SessionCard({ session, onPress }: SessionCardProps) {
  const formatDuration = (startedAt: string, endedAt?: string): string => {
    if (!endedAt) return 'Lopend...';
    const start = new Date(startedAt);
    const end = new Date(endedAt);
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}u ${minutes % 60}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active':
        return '#10b981';
      case 'completed':
        return '#3b82f6';
      case 'cancelled':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'active':
        return 'Actief';
      case 'completed':
        return 'Voltooid';
      case 'cancelled':
        return 'Geannuleerd';
      default:
        return status;
    }
  };

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <ThemedView
        style={[
          styles.card,
          session.status === 'active' && styles.cardActive,
        ]}>
        <View style={styles.header}>
          <View style={styles.dateTime}>
            <ThemedText type="defaultSemiBold" style={styles.date}>
              {format(new Date(session.started_at), 'dd MMM yyyy', { locale: nl })}
            </ThemedText>
            <ThemedText style={styles.time}>
              {format(new Date(session.started_at), 'HH:mm', { locale: nl })}
            </ThemedText>
          </View>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getStatusColor(session.status) },
            ]}>
            <ThemedText style={styles.statusText}>
              {getStatusText(session.status)}
            </ThemedText>
          </View>
        </View>

        {session.technique_name && (
          <View style={styles.techniqueRow}>
            <IconSymbol name="lungs.fill" size={16} color="#3b82f6" />
            <ThemedText style={styles.technique}>{session.technique_name}</ThemedText>
          </View>
        )}

        <View style={styles.footer}>
          <View style={styles.footerItem}>
            <IconSymbol name="clock" size={14} color="#6b7280" />
            <ThemedText style={styles.footerText}>
              {formatDuration(session.started_at, session.ended_at)}
            </ThemedText>
          </View>
          {session.target_rr && (
            <View style={styles.footerItem}>
              <IconSymbol name="target" size={14} color="#6b7280" />
              <ThemedText style={styles.footerText}>
                Doel: {session.target_rr.toFixed(1)} bpm
              </ThemedText>
            </View>
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
    borderLeftColor: '#3b82f6',
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.2)',
  },
  cardActive: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderLeftColor: '#10b981',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  dateTime: {
    flex: 1,
  },
  date: {
    fontSize: 16,
    marginBottom: 2,
  },
  time: {
    fontSize: 14,
    opacity: 0.7,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 11,
    color: '#fff',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  techniqueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  technique: {
    fontSize: 14,
    opacity: 0.8,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  footerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  footerText: {
    fontSize: 12,
    opacity: 0.7,
  },
});
