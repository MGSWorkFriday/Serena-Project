/**
 * Session Detail Modal Component
 * Shows detailed information about a session
 */
import { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import { apiClient } from '@/services/api';
import type { Session, SignalRecord } from '@/services/api/types';

interface SessionDetailProps {
  session: Session | null;
  visible: boolean;
  onClose: () => void;
}

interface SessionStats {
  avgHR?: number;
  avgRR?: number;
  minHR?: number;
  maxHR?: number;
  minRR?: number;
  maxRR?: number;
}

export function SessionDetail({ session, visible, onClose }: SessionDetailProps) {
  const [stats, setStats] = useState<SessionStats>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (session && visible) {
      loadStats();
    } else {
      setStats({});
    }
  }, [session, visible]);

  const loadStats = async () => {
    if (!session) return;

    setLoading(true);
    try {
      const startTs = new Date(session.started_at).getTime();
      const endTs = session.ended_at
        ? new Date(session.ended_at).getTime()
        : Date.now();

      // Fetch HR signals
      const hrSignals = await apiClient.getSignals({
        session_id: session.session_id,
        signal: 'hr_derived',
        start_ts: startTs,
        end_ts: endTs,
        limit: 10000,
      });

      // Fetch RR signals
      const rrSignals = await apiClient.getSignals({
        session_id: session.session_id,
        signal: 'resp_rr',
        start_ts: startTs,
        end_ts: endTs,
        limit: 10000,
      });

      // Calculate HR statistics
      const hrValues = hrSignals
        .map((s) => s.bpm)
        .filter((bpm): bpm is number => bpm !== undefined && bpm > 0);

      // Calculate RR statistics
      const rrValues = rrSignals
        .map((s) => s.estRR)
        .filter((rr): rr is number => rr !== undefined && rr > 0);

      if (hrValues.length > 0) {
        const sum = hrValues.reduce((a, b) => a + b, 0);
        setStats((prev) => ({
          ...prev,
          avgHR: sum / hrValues.length,
          minHR: Math.min(...hrValues),
          maxHR: Math.max(...hrValues),
        }));
      }

      if (rrValues.length > 0) {
        const sum = rrValues.reduce((a, b) => a + b, 0);
        setStats((prev) => ({
          ...prev,
          avgRR: sum / rrValues.length,
          minRR: Math.min(...rrValues),
          maxRR: Math.max(...rrValues),
        }));
      }
    } catch (error) {
      console.error('Failed to load session stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!session) return null;

  const formatDuration = (startedAt: string, endedAt?: string): string => {
    if (!endedAt) return 'Lopend...';
    const start = new Date(startedAt);
    const end = new Date(endedAt);
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours} uur ${minutes % 60} minuten`;
    }
    if (minutes > 0) {
      return `${minutes} minuten ${seconds % 60} seconden`;
    }
    return `${seconds} seconden`;
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
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}>
      <ThemedView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <IconSymbol name="xmark" size={24} color="#fff" />
          </TouchableOpacity>
          <ThemedText type="title" style={styles.title}>
            Sessie Details
          </ThemedText>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Status Card */}
          <View style={[styles.statusCard, { borderLeftColor: getStatusColor(session.status) }]}>
            <View style={styles.statusRow}>
              <View
                style={[
                  styles.statusBadge,
                  { backgroundColor: getStatusColor(session.status) },
                ]}>
                <ThemedText style={styles.statusText}>
                  {getStatusText(session.status)}
                </ThemedText>
              </View>
              <ThemedText style={styles.sessionId}>
                ID: {session.session_id}
              </ThemedText>
            </View>
          </View>

          {/* Date & Time */}
          <View style={styles.section}>
            <ThemedText type="subtitle" style={styles.sectionTitle}>
              Datum & Tijd
            </ThemedText>
            <View style={styles.infoRow}>
              <IconSymbol name="calendar" size={20} color="#3b82f6" />
              <View style={styles.infoContent}>
                <ThemedText style={styles.infoLabel}>Gestart</ThemedText>
                <ThemedText type="defaultSemiBold">
                  {format(new Date(session.started_at), 'EEEE d MMMM yyyy, HH:mm', { locale: nl })}
                </ThemedText>
              </View>
            </View>
            {session.ended_at && (
              <View style={styles.infoRow}>
                <IconSymbol name="calendar.badge.checkmark" size={20} color="#10b981" />
                <View style={styles.infoContent}>
                  <ThemedText style={styles.infoLabel}>Beëindigd</ThemedText>
                  <ThemedText type="defaultSemiBold">
                    {format(new Date(session.ended_at), 'EEEE d MMMM yyyy, HH:mm', { locale: nl })}
                  </ThemedText>
                </View>
              </View>
            )}
            <View style={styles.infoRow}>
              <IconSymbol name="clock" size={20} color="#f59e0b" />
              <View style={styles.infoContent}>
                <ThemedText style={styles.infoLabel}>Duur</ThemedText>
                <ThemedText type="defaultSemiBold">
                  {formatDuration(session.started_at, session.ended_at)}
                </ThemedText>
              </View>
            </View>
          </View>

          {/* Technique */}
          {session.technique_name && (
            <View style={styles.section}>
              <ThemedText type="subtitle" style={styles.sectionTitle}>
                Techniek
              </ThemedText>
              <View style={styles.infoRow}>
                <IconSymbol name="lungs.fill" size={20} color="#3b82f6" />
                <ThemedText type="defaultSemiBold" style={styles.technique}>
                  {session.technique_name}
                </ThemedText>
              </View>
            </View>
          )}

          {/* Target */}
          {session.target_rr && (
            <View style={styles.section}>
              <ThemedText type="subtitle" style={styles.sectionTitle}>
                Doelstelling
              </ThemedText>
              <View style={styles.infoRow}>
                <IconSymbol name="target" size={20} color="#3b82f6" />
                <ThemedText type="defaultSemiBold" style={styles.target}>
                  {session.target_rr.toFixed(1)} ademhalingen per minuut
                </ThemedText>
              </View>
            </View>
          )}

          {/* Statistics */}
          <View style={styles.section}>
            <ThemedText type="subtitle" style={styles.sectionTitle}>
              Statistieken
            </ThemedText>
            {loading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color="#3b82f6" />
                <ThemedText style={styles.loadingText}>Statistieken laden...</ThemedText>
              </View>
            ) : (
              <>
                {stats.avgHR !== undefined && (
                  <View style={styles.statsCard}>
                    <ThemedText type="defaultSemiBold" style={styles.statsTitle}>
                      Hartslag (BPM)
                    </ThemedText>
                    <View style={styles.statsGrid}>
                      <View style={styles.statItem}>
                        <ThemedText style={styles.statLabel}>Gemiddeld</ThemedText>
                        <ThemedText type="defaultSemiBold" style={styles.statValue}>
                          {stats.avgHR.toFixed(1)}
                        </ThemedText>
                      </View>
                      {stats.minHR !== undefined && (
                        <View style={styles.statItem}>
                          <ThemedText style={styles.statLabel}>Minimum</ThemedText>
                          <ThemedText type="defaultSemiBold" style={styles.statValue}>
                            {stats.minHR.toFixed(1)}
                          </ThemedText>
                        </View>
                      )}
                      {stats.maxHR !== undefined && (
                        <View style={styles.statItem}>
                          <ThemedText style={styles.statLabel}>Maximum</ThemedText>
                          <ThemedText type="defaultSemiBold" style={styles.statValue}>
                            {stats.maxHR.toFixed(1)}
                          </ThemedText>
                        </View>
                      )}
                    </View>
                  </View>
                )}

                {stats.avgRR !== undefined && (
                  <View style={styles.statsCard}>
                    <ThemedText type="defaultSemiBold" style={styles.statsTitle}>
                      Ademhalingsfrequentie (BPM)
                    </ThemedText>
                    <View style={styles.statsGrid}>
                      <View style={styles.statItem}>
                        <ThemedText style={styles.statLabel}>Gemiddeld</ThemedText>
                        <ThemedText type="defaultSemiBold" style={styles.statValue}>
                          {stats.avgRR.toFixed(1)}
                        </ThemedText>
                      </View>
                      {stats.minRR !== undefined && (
                        <View style={styles.statItem}>
                          <ThemedText style={styles.statLabel}>Minimum</ThemedText>
                          <ThemedText type="defaultSemiBold" style={styles.statValue}>
                            {stats.minRR.toFixed(1)}
                          </ThemedText>
                        </View>
                      )}
                      {stats.maxRR !== undefined && (
                        <View style={styles.statItem}>
                          <ThemedText style={styles.statLabel}>Maximum</ThemedText>
                          <ThemedText type="defaultSemiBold" style={styles.statValue}>
                            {stats.maxRR.toFixed(1)}
                          </ThemedText>
                        </View>
                      )}
                    </View>
                  </View>
                )}

                {stats.avgHR === undefined && stats.avgRR === undefined && (
                  <ThemedText style={styles.noStats}>
                    Geen statistieken beschikbaar voor deze sessie
                  </ThemedText>
                )}
              </>
            )}
          </View>

          {/* Metadata */}
          {session.metadata && Object.keys(session.metadata).length > 0 && (
            <View style={styles.section}>
              <ThemedText type="subtitle" style={styles.sectionTitle}>
                Extra Informatie
              </ThemedText>
              <ThemedView style={styles.metadataCard}>
                <ThemedText style={styles.metadataText}>
                  {JSON.stringify(session.metadata, null, 2)}
                </ThemedText>
              </ThemedView>
            </View>
          )}
        </ScrollView>
      </ThemedView>
    </Modal>
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
  closeButton: {
    padding: 8,
  },
  title: {
    flex: 1,
    textAlign: 'center',
    fontSize: 20,
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  statusCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    borderLeftWidth: 4,
    marginBottom: 20,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  sessionId: {
    fontSize: 11,
    opacity: 0.6,
    fontFamily: 'monospace',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 2,
  },
  technique: {
    fontSize: 16,
  },
  target: {
    fontSize: 16,
  },
  statsCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    marginBottom: 12,
  },
  statsTitle: {
    fontSize: 16,
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 20,
    color: '#3b82f6',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 20,
  },
  loadingText: {
    opacity: 0.7,
  },
  noStats: {
    opacity: 0.6,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  metadataCard: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(128, 128, 128, 0.05)',
  },
  metadataText: {
    fontSize: 11,
    fontFamily: 'monospace',
    opacity: 0.8,
  },
});
