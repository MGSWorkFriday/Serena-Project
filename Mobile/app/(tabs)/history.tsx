/**
 * Session History Screen
 * List of past sessions with filters
 */
import { useState, useMemo } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { SessionCard } from '@/components/history/SessionCard';
import { SessionDetail } from '@/components/history/SessionDetail';
import { useSessions } from '@/hooks/useSessions';
import { useBluetooth } from '@/hooks/useBluetooth';
import { useTechniques } from '@/hooks/useTechniques';
import type { Session } from '@/services/api/types';

export default function HistoryScreen() {
  const { deviceId } = useBluetooth();
  const { data: sessions, isLoading, refetch, isRefetching } = useSessions(deviceId || undefined);
  const { data: techniques } = useTechniques(true);

  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'completed' | 'cancelled'>('all');
  const [techniqueFilter, setTechniqueFilter] = useState<string>('all');

  // Filter sessions
  const filteredSessions = useMemo(() => {
    if (!sessions) return [];

    let filtered = [...sessions];

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((s) => s.status === statusFilter);
    }

    // Technique filter
    if (techniqueFilter !== 'all') {
      filtered = filtered.filter((s) => s.technique_name === techniqueFilter);
    }

    // Search query (search in technique name)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (s) =>
          s.technique_name?.toLowerCase().includes(query) ||
          s.session_id.toLowerCase().includes(query)
      );
    }

    // Sort by date (newest first)
    filtered.sort((a, b) => {
      const dateA = new Date(a.started_at).getTime();
      const dateB = new Date(b.started_at).getTime();
      return dateB - dateA;
    });

    return filtered;
  }, [sessions, statusFilter, techniqueFilter, searchQuery]);

  const handleSessionPress = (session: Session) => {
    setSelectedSession(session);
  };

  const handleCloseDetail = () => {
    setSelectedSession(null);
  };

  const uniqueTechniques = useMemo(() => {
    if (!sessions) return [];
    const techniques = new Set<string>();
    sessions.forEach((s) => {
      if (s.technique_name) {
        techniques.add(s.technique_name);
      }
    });
    return Array.from(techniques).sort();
  }, [sessions]);

  const renderSession = ({ item }: { item: Session }) => (
    <SessionCard session={item} onPress={() => handleSessionPress(item)} />
  );

  const renderEmpty = () => {
    if (isLoading) {
      return (
        <View style={styles.emptyContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <ThemedText style={styles.emptyText}>Sessies laden...</ThemedText>
        </View>
      );
    }

    if (filteredSessions.length === 0 && sessions && sessions.length > 0) {
      return (
        <View style={styles.emptyContainer}>
          <IconSymbol name="magnifyingglass" size={48} color="#6b7280" />
          <ThemedText type="subtitle" style={styles.emptyText}>
            Geen sessies gevonden
          </ThemedText>
          <ThemedText style={styles.emptySubtext}>
            Probeer andere filters of zoektermen
          </ThemedText>
        </View>
      );
    }

    return (
      <View style={styles.emptyContainer}>
        <IconSymbol name="clock" size={48} color="#6b7280" />
        <ThemedText type="subtitle" style={styles.emptyText}>
          Nog geen sessies
        </ThemedText>
        <ThemedText style={styles.emptySubtext}>
          Start een ademhalingsoefening om sessies te zien
        </ThemedText>
      </View>
    );
  };

  return (
    <ThemedView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <ThemedText type="title" style={styles.title}>
          Sessie Geschiedenis
        </ThemedText>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <IconSymbol name="magnifyingglass" size={20} color="#6b7280" />
        <TextInput
          style={styles.searchInput}
          placeholder="Zoek op techniek of sessie ID..."
          placeholderTextColor="#6b7280"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <IconSymbol name="xmark.circle.fill" size={20} color="#6b7280" />
          </TouchableOpacity>
        )}
      </View>

      {/* Filters */}
      <View style={styles.filtersContainer}>
        {/* Status Filter */}
        <View style={styles.filterGroup}>
          <ThemedText style={styles.filterLabel}>Status:</ThemedText>
          <View style={styles.filterButtons}>
            {(['all', 'active', 'completed', 'cancelled'] as const).map((status) => (
              <TouchableOpacity
                key={status}
                onPress={() => setStatusFilter(status)}
                style={[
                  styles.filterButton,
                  statusFilter === status && styles.filterButtonActive,
                ]}>
                <ThemedText
                  style={[
                    styles.filterButtonText,
                    statusFilter === status && styles.filterButtonTextActive,
                  ]}>
                  {status === 'all' ? 'Alles' : status === 'active' ? 'Actief' : status === 'completed' ? 'Voltooid' : 'Geannuleerd'}
                </ThemedText>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Technique Filter */}
        {uniqueTechniques.length > 0 && (
          <View style={styles.filterGroup}>
            <ThemedText style={styles.filterLabel}>Techniek:</ThemedText>
            <View style={styles.filterButtons}>
              <TouchableOpacity
                onPress={() => setTechniqueFilter('all')}
                style={[
                  styles.filterButton,
                  techniqueFilter === 'all' && styles.filterButtonActive,
                ]}>
                <ThemedText
                  style={[
                    styles.filterButtonText,
                    techniqueFilter === 'all' && styles.filterButtonTextActive,
                  ]}>
                  Alles
                </ThemedText>
              </TouchableOpacity>
              {uniqueTechniques.map((technique) => (
                <TouchableOpacity
                  key={technique}
                  onPress={() => setTechniqueFilter(technique)}
                  style={[
                    styles.filterButton,
                    techniqueFilter === technique && styles.filterButtonActive,
                  ]}>
                  <ThemedText
                    style={[
                      styles.filterButtonText,
                      techniqueFilter === technique && styles.filterButtonTextActive,
                    ]}
                    numberOfLines={1}>
                    {technique}
                  </ThemedText>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </View>

      {/* Session List */}
      <FlatList
        data={filteredSessions}
        renderItem={renderSession}
        keyExtractor={(item) => item.session_id}
        contentContainerStyle={[
          styles.listContent,
          filteredSessions.length === 0 && styles.listContentEmpty,
        ]}
        ListEmptyComponent={renderEmpty}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor="#3b82f6"
          />
        }
        showsVerticalScrollIndicator={false}
      />

      {/* Session Detail Modal */}
      <SessionDetail
        session={selectedSession}
        visible={selectedSession !== null}
        onClose={handleCloseDetail}
      />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingBottom: 12,
  },
  title: {
    fontSize: 28,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginHorizontal: 16,
    marginBottom: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#fff',
  },
  filtersContainer: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  filterGroup: {
    marginBottom: 12,
  },
  filterLabel: {
    fontSize: 14,
    opacity: 0.7,
    marginBottom: 8,
  },
  filterButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: 'rgba(128, 128, 128, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.3)',
  },
  filterButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  filterButtonText: {
    fontSize: 13,
    opacity: 0.8,
  },
  filterButtonTextActive: {
    color: '#fff',
    opacity: 1,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
    paddingTop: 8,
  },
  listContentEmpty: {
    flex: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    marginTop: 16,
    textAlign: 'center',
    opacity: 0.8,
  },
  emptySubtext: {
    marginTop: 8,
    textAlign: 'center',
    opacity: 0.6,
    fontSize: 14,
  },
});
