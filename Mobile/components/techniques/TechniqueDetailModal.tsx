/**
 * Technique Detail Modal Component
 * Shows full details of a breathing technique
 */
import { View, StyleSheet, Modal, ScrollView, TouchableOpacity } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import type { Technique } from '@/services/api/types';

interface TechniqueDetailModalProps {
  technique: Technique | null;
  visible: boolean;
  onClose: () => void;
  onStart?: () => void;
}

/**
 * Format protocol array to detailed view
 * Supports both array format [[in, hold1, out, hold2, repeats], ...] and object format
 */
function formatProtocolDetailed(protocol: any): Array<{
  phase: string;
  in: number;
  hold1: number;
  out: number;
  hold2: number;
  repeats: number;
  total: number;
}> {
  if (!protocol) {
    return [];
  }

  // Handle array format: [[in, hold1, out, hold2, repeats], ...]
  if (Array.isArray(protocol)) {
    return protocol.map((row, index) => {
      if (!Array.isArray(row) || row.length < 4) {
        return {
          phase: `Fase ${index + 1}`,
          in: 0,
          hold1: 0,
          out: 0,
          hold2: 0,
          repeats: 0,
          total: 0,
        };
      }

      const [inTime, hold1, outTime, hold2, repeats = 1] = row;
      const total = (inTime + hold1 + outTime + hold2) * repeats;

      return {
        phase: `Fase ${index + 1}`,
        in: inTime,
        hold1: hold1 || 0,
        out: outTime,
        hold2: hold2 || 0,
        repeats,
        total,
      };
    });
  }

  // Handle object format (legacy): { in, hold1, out, hold2 }
  if (typeof protocol === 'object' && !Array.isArray(protocol)) {
    const inTime = protocol.in || 0;
    const hold1 = protocol.hold1 || 0;
    const outTime = protocol.out || 0;
    const hold2 = protocol.hold2 || 0;
    const repeats = 1;
    const total = inTime + hold1 + outTime + hold2;

    return [
      {
        phase: 'Fase 1',
        in: inTime,
        hold1,
        out: outTime,
        hold2,
        repeats,
        total,
      },
    ];
  }

  return [];
}

export function TechniqueDetailModal({
  technique,
  visible,
  onClose,
  onStart,
}: TechniqueDetailModalProps) {
  if (!technique) return null;

  const protocolDetails = formatProtocolDetailed(technique.protocol);

  return (
    <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <ThemedView style={styles.modal}>
          {/* Header */}
          <View style={styles.header}>
            <ThemedText type="title" style={styles.title}>
              {technique.name}
            </ThemedText>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <IconSymbol name="xmark.circle.fill" size={28} color="#6b7280" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Description */}
            {technique.description && (
              <View style={styles.section}>
                <ThemedText type="subtitle" style={styles.sectionTitle}>
                  Beschrijving
                </ThemedText>
                <ThemedText style={styles.description}>{technique.description}</ThemedText>
              </View>
            )}

            {/* Protocol Details */}
            <View style={styles.section}>
              <ThemedText type="subtitle" style={styles.sectionTitle}>
                Protocol
              </ThemedText>
              {protocolDetails.length > 0 ? (
                protocolDetails.map((phase, index) => (
                  <View key={index} style={styles.protocolCard}>
                    <ThemedText type="defaultSemiBold" style={styles.phaseTitle}>
                      {phase.phase}
                    </ThemedText>
                    <View style={styles.protocolRow}>
                      <View style={styles.protocolItem}>
                        <ThemedText style={styles.protocolLabel}>In</ThemedText>
                        <ThemedText style={styles.protocolValue}>{phase.in}s</ThemedText>
                      </View>
                      {phase.hold1 > 0 && (
                        <View style={styles.protocolItem}>
                          <ThemedText style={styles.protocolLabel}>Hold</ThemedText>
                          <ThemedText style={styles.protocolValue}>{phase.hold1}s</ThemedText>
                        </View>
                      )}
                      <View style={styles.protocolItem}>
                        <ThemedText style={styles.protocolLabel}>Uit</ThemedText>
                        <ThemedText style={styles.protocolValue}>{phase.out}s</ThemedText>
                      </View>
                      {phase.hold2 > 0 && (
                        <View style={styles.protocolItem}>
                          <ThemedText style={styles.protocolLabel}>Hold</ThemedText>
                          <ThemedText style={styles.protocolValue}>{phase.hold2}s</ThemedText>
                        </View>
                      )}
                      {phase.repeats > 1 && (
                        <View style={styles.protocolItem}>
                          <ThemedText style={styles.protocolLabel}>Herhalingen</ThemedText>
                          <ThemedText style={styles.protocolValue}>{phase.repeats}x</ThemedText>
                        </View>
                      )}
                    </View>
                    <ThemedText style={styles.totalTime}>
                      Totaal: {Math.round(phase.total)}s ({Math.round(phase.total / 60)}m)
                    </ThemedText>
                  </View>
                ))
              ) : (
                <ThemedText style={styles.noProtocol}>Geen protocol gedefinieerd</ThemedText>
              )}
            </View>

            {/* Metadata */}
            <View style={styles.section}>
              <ThemedText type="subtitle" style={styles.sectionTitle}>
                Informatie
              </ThemedText>
              <View style={styles.metadataRow}>
                <ThemedText style={styles.metadataLabel}>Parameter versie:</ThemedText>
                <ThemedText style={styles.metadataValue}>
                  {technique.param_version || 'Default'}
                </ThemedText>
              </View>
              <View style={styles.metadataRow}>
                <ThemedText style={styles.metadataLabel}>Status:</ThemedText>
                <ThemedText style={styles.metadataValue}>
                  {technique.is_active ? 'Actief' : 'Inactief'}
                </ThemedText>
              </View>
            </View>
          </ScrollView>

          {/* Footer Actions */}
          {onStart && (
            <View style={styles.footer}>
              <TouchableOpacity onPress={onClose} style={styles.cancelButton}>
                <ThemedText style={styles.cancelButtonText}>Sluiten</ThemedText>
              </TouchableOpacity>
              <TouchableOpacity onPress={onStart} style={styles.startButton}>
                <IconSymbol name="play.fill" size={20} color="#fff" />
                <ThemedText style={styles.startButtonText}>Start Sessie</ThemedText>
              </TouchableOpacity>
            </View>
          )}
        </ThemedView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modal: {
    maxHeight: '90%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(128, 128, 128, 0.2)',
  },
  title: {
    flex: 1,
    fontSize: 22,
  },
  closeButton: {
    padding: 4,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: 12,
  },
  description: {
    fontSize: 15,
    lineHeight: 22,
    opacity: 0.9,
  },
  protocolCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    marginBottom: 12,
  },
  phaseTitle: {
    fontSize: 16,
    marginBottom: 12,
  },
  protocolRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 8,
  },
  protocolItem: {
    alignItems: 'center',
    minWidth: 60,
  },
  protocolLabel: {
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 4,
  },
  protocolValue: {
    fontSize: 18,
    fontWeight: '600',
  },
  totalTime: {
    fontSize: 13,
    opacity: 0.7,
    marginTop: 8,
    textAlign: 'center',
  },
  noProtocol: {
    fontSize: 14,
    opacity: 0.6,
    fontStyle: 'italic',
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(128, 128, 128, 0.1)',
  },
  metadataLabel: {
    fontSize: 14,
    opacity: 0.7,
  },
  metadataValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    gap: 12,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  cancelButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.2)',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  startButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#10b981',
  },
  startButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
