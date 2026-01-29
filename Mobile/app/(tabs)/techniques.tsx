/**
 * Techniques Selection Screen
 * List of available breathing techniques
 */
import { useState, useMemo, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Modal,
  ActivityIndicator,
  Pressable,
} from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { TechniqueDetailModal } from '@/components/techniques/TechniqueDetailModal';
import { useTechniques } from '@/hooks/useTechniques';
import { useBluetooth } from '@/hooks/useBluetooth';
import { config } from '@/constants/config';
import { useCreateSession, useEndSession, useSessions } from '@/hooks/useSessions';
import { router } from 'expo-router';
import type { Technique } from '@/services/api/types';

export default function TechniquesScreen() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');
  const [selectedTechnique, setSelectedTechnique] = useState<Technique | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const { deviceId, connected } = useBluetooth();
  const createSessionMutation = useCreateSession();
  const endSessionMutation = useEndSession();
  
  // Get active sessions to close before starting new one
  const { data: activeSessions } = useSessions({ deviceId: deviceId || undefined, status: 'active' });

  const { data: techniques, isLoading, isError, error, refetch } = useTechniques(true);

  useEffect(() => {
    if (__DEV__ && isError && error) {
      console.error('[Techniques] load error:', (error as Error)?.message, error);
    }
  }, [isError, error]);

  const filteredForDropdown = useMemo(() => {
    if (!techniques) return [];
    if (!filterQuery.trim()) return techniques;
    const q = filterQuery.trim().toLowerCase();
    return techniques.filter(
      (t) =>
        t.name.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q)
    );
  }, [techniques, filterQuery]);

  const handleSelectTechnique = (t: Technique) => {
    setSelectedTechnique(t);
    setDropdownOpen(false);
    setFilterQuery('');
    setDetailModalVisible(true);
  };

  const handleStartSession = async () => {
    if (!selectedTechnique || !deviceId) {
      return;
    }

    try {
      // Close any active sessions first
      if (activeSessions && activeSessions.length > 0) {
        console.log('[Techniques] Closing active sessions before starting new one');
        for (const activeSession of activeSessions) {
          try {
            await endSessionMutation.mutateAsync(activeSession.session_id);
          } catch (err) {
            console.warn('[Techniques] Failed to end session:', activeSession.session_id, err);
          }
        }
      }

      // Create session with technique
      const session = await createSessionMutation.mutateAsync({
        device_id: deviceId,
        technique_name: selectedTechnique.name,
        param_version: selectedTechnique.param_version || 'Default',
        metadata: {
          technique_id: selectedTechnique._id,
          protocol: selectedTechnique.protocol,
        },
      });

      setDetailModalVisible(false);
      router.push(`/session?sessionId=${session.session_id}`);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  if (isLoading) {
    return (
      <ThemedView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" />
          <ThemedText style={styles.loadingText}>Technieken laden...</ThemedText>
        </View>
      </ThemedView>
    );
  }

  const hasTechniques = Array.isArray(techniques) && techniques.length > 0;

  return (
    <ThemedView style={styles.container}>
      <View style={styles.header}>
        <ThemedText type="title" style={styles.title}>
          Ademhalingstechnieken
        </ThemedText>
        {!connected && (
          <ThemedText style={styles.warning}>Verbind eerst een device om te starten</ThemedText>
        )}
      </View>

      {/* Dropdown / combobox */}
      <View style={styles.dropdownSection}>
        <ThemedText style={styles.label}>Techniek</ThemedText>
        <Pressable
          style={[styles.dropdown, !hasTechniques && styles.dropdownDisabled]}
          onPress={() => hasTechniques && setDropdownOpen(true)}
          disabled={!hasTechniques}>
          <ThemedText
            style={[styles.dropdownText, !selectedTechnique && styles.dropdownPlaceholder]}
            numberOfLines={1}>
            {selectedTechnique ? selectedTechnique.name : 'Kies een techniek...'}
          </ThemedText>
          <IconSymbol name="chevron.down" size={18} color="#6b7280" />
        </Pressable>
      </View>

      {/* Modal: lijst om uit te kiezen */}
      <Modal
        visible={dropdownOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setDropdownOpen(false)}>
        <Pressable style={styles.modalBackdrop} onPress={() => setDropdownOpen(false)}>
          <Pressable style={styles.modalContent} onPress={(e) => e.stopPropagation()}>
            <View style={styles.modalHeader}>
              <ThemedText type="subtitle">Selecteer techniek</ThemedText>
              <TouchableOpacity onPress={() => setDropdownOpen(false)} hitSlop={12}>
                <IconSymbol name="xmark.circle.fill" size={24} color="#9ca3af" />
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.filterInput}
              placeholder="Filter op naam..."
              placeholderTextColor="#9ca3af"
              value={filterQuery}
              onChangeText={setFilterQuery}
            />
            <ScrollView style={styles.modalList} keyboardShouldPersistTaps="handled">
              {filteredForDropdown.length === 0 ? (
                <ThemedText style={styles.modalEmpty}>
                  {filterQuery ? 'Geen technieken gevonden' : 'Geen technieken'}
                </ThemedText>
              ) : (
                filteredForDropdown.map((t) => (
                  <TouchableOpacity
                    key={String(t._id ?? t.name)}
                    style={styles.modalItem}
                    onPress={() => handleSelectTechnique(t)}
                    activeOpacity={0.7}>
                    <ThemedText style={styles.modalItemText}>{t.name}</ThemedText>
                    <IconSymbol name="chevron.right" size={14} color="#9ca3af" />
                  </TouchableOpacity>
                ))
              )}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Lege of fout-state */}
      {!hasTechniques && (
        <View style={styles.emptyContainer}>
          <IconSymbol name="lungs" size={48} color="#6b7280" />
          <ThemedText style={styles.emptyText}>
            {isError ? 'Kon technieken niet laden' : 'Geen technieken beschikbaar'}
          </ThemedText>
          {isError && (
            <ThemedText style={styles.emptyHint}>
              Controleer of de backend op {config.api.baseUrl} draait. Bij Expo Web: sta CORS toe
              voor deze origin. De app gebruikt /techniques/public. Open de console (F12) voor de
              exacte fout.
            </ThemedText>
          )}
          {!isError && (
            <ThemedText style={styles.emptyHint}>
              In MongoDB moeten technieken show_in_app en is_active op true hebben. Draai het
              migratiescript of werk ze in Compass bij.
            </ThemedText>
          )}
          <TouchableOpacity style={styles.refetchBtn} onPress={() => refetch()}>
            <ThemedText style={styles.refetchBtnText}>Opnieuw laden</ThemedText>
          </TouchableOpacity>
        </View>
      )}

      {/* Knop details & starten zodra er een techniek gekozen is */}
      {hasTechniques && selectedTechnique && !dropdownOpen && (
        <TouchableOpacity style={styles.openDetailBtn} onPress={() => setDetailModalVisible(true)}>
          <ThemedText style={styles.openDetailBtnText}>Details & starten</ThemedText>
          <IconSymbol name="chevron.right" size={18} color="#3b82f6" />
        </TouchableOpacity>
      )}

      <TechniqueDetailModal
        technique={selectedTechnique}
        visible={detailModalVisible}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedTechnique(null);
        }}
        onStart={connected && deviceId ? handleStartSession : undefined}
      />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    opacity: 0.7,
  },
  header: {
    padding: 20,
    paddingBottom: 12,
  },
  title: {
    fontSize: 28,
    marginBottom: 8,
  },
  warning: {
    fontSize: 14,
    color: '#f59e0b',
    marginTop: 4,
  },
  // Dropdown / combobox
  dropdownSection: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  label: {
    fontSize: 14,
    marginBottom: 6,
    opacity: 0.85,
  },
  dropdown: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.3)',
    borderRadius: 10,
    backgroundColor: 'rgba(128, 128, 128, 0.08)',
  },
  dropdownDisabled: {
    opacity: 0.6,
  },
  dropdownText: {
    fontSize: 16,
    flex: 1,
    marginRight: 8,
  },
  dropdownPlaceholder: {
    opacity: 0.6,
  },
  // Modal: techniek kiezen
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
    backgroundColor: '#f9fafb',
    borderRadius: 16,
    overflow: 'hidden',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(128, 128, 128, 0.2)',
  },
  filterInput: {
    marginHorizontal: 12,
    marginBottom: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    fontSize: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.25)',
    backgroundColor: '#ffffff',
    color: '#111827',
  },
  modalList: {
    maxHeight: 300,
    paddingBottom: 16,
  },
  modalEmpty: {
    padding: 24,
    textAlign: 'center',
    opacity: 0.6,
  },
  modalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(128, 128, 128, 0.1)',
  },
  modalItemText: {
    fontSize: 16,
  },
  // Lege / fout-state
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 24,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
    opacity: 0.6,
    textAlign: 'center',
  },
  emptyHint: {
    fontSize: 13,
    opacity: 0.6,
    textAlign: 'center',
  },
  refetchBtn: {
    marginTop: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  refetchBtnText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#3b82f6',
  },
  // Details & starten
  openDetailBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginHorizontal: 20,
    marginTop: 20,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  openDetailBtnText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3b82f6',
  },
});
