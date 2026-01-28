/**
 * Technique Card Component
 * Displays a single breathing technique with preview
 */
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import type { Technique } from '@/services/api/types';

interface TechniqueCardProps {
  technique: Technique;
  onPress: () => void;
  onInfoPress?: () => void;
}

/**
 * Format protocol array to readable string
 * Protocol format: [[in, hold1, out, hold2, repeats], ...]
 */
function formatProtocol(protocol: any): string {
  if (!protocol) {
    return 'Geen protocol';
  }

  // Handle array format: [[in, hold1, out, hold2, repeats], ...]
  if (Array.isArray(protocol) && protocol.length > 0) {
    const firstRow = protocol[0];
    if (Array.isArray(firstRow) && firstRow.length >= 4) {
      const [inTime, hold1, outTime, hold2, repeats] = firstRow;
      const parts: string[] = [];

      if (inTime > 0) parts.push(`In: ${inTime}s`);
      if (hold1 > 0) parts.push(`Hold: ${hold1}s`);
      if (outTime > 0) parts.push(`Uit: ${outTime}s`);
      if (hold2 > 0) parts.push(`Hold: ${hold2}s`);
      if (repeats && repeats > 0) parts.push(`${repeats}x`);

      return parts.join(' • ') || 'Geen protocol';
    }
  }

  // Handle object format (legacy): { in, hold1, out, hold2 }
  if (typeof protocol === 'object' && !Array.isArray(protocol)) {
    const parts: string[] = [];
    if (protocol.in > 0) parts.push(`In: ${protocol.in}s`);
    if (protocol.hold1 > 0) parts.push(`Hold: ${protocol.hold1}s`);
    if (protocol.out > 0) parts.push(`Uit: ${protocol.out}s`);
    if (protocol.hold2 > 0) parts.push(`Hold: ${protocol.hold2}s`);
    return parts.join(' • ') || 'Geen protocol';
  }

  return 'Ongeldig protocol';
}

export function TechniqueCard({ technique, onPress, onInfoPress }: TechniqueCardProps) {
  const protocolText = formatProtocol(technique.protocol);

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <ThemedView style={styles.card}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <ThemedText type="defaultSemiBold" style={styles.title}>
              {technique.name}
            </ThemedText>
            {onInfoPress && (
              <TouchableOpacity
                onPress={(e) => {
                  e.stopPropagation();
                  onInfoPress();
                }}
                style={styles.infoButton}>
                <IconSymbol name="info.circle" size={20} color="#3b82f6" />
              </TouchableOpacity>
            )}
          </View>
        </View>

        {technique.description && (
          <ThemedText style={styles.description} numberOfLines={2}>
            {technique.description}
          </ThemedText>
        )}

        <View style={styles.protocolRow}>
          <IconSymbol name="clock.fill" size={16} color="#6b7280" />
          <ThemedText style={styles.protocol}>{protocolText}</ThemedText>
        </View>

        <View style={styles.footer}>
          <View style={styles.badge}>
            <ThemedText style={styles.badgeText}>
              {technique.is_active ? 'Actief' : 'Inactief'}
            </ThemedText>
          </View>
          <IconSymbol name="chevron.right" size={20} color="#6b7280" />
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
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.2)',
  },
  header: {
    marginBottom: 8,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: 18,
    flex: 1,
  },
  infoButton: {
    padding: 4,
    marginLeft: 8,
  },
  description: {
    fontSize: 14,
    opacity: 0.8,
    marginBottom: 12,
    lineHeight: 20,
  },
  protocolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  protocol: {
    fontSize: 13,
    opacity: 0.7,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
  },
  badgeText: {
    fontSize: 11,
    color: '#10b981',
    fontWeight: '600',
  },
});
