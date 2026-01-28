/**
 * Offline Indicator
 *
 * "Offline" = de periodieke verbindingstest (GET /api/v1/ping) is mislukt.
 * Dat zegt niets over andere verzoeken: technieken, sessies, enz. kunnen wél
 * slagen (bijv. als de backend net opstartte). Bij een geslaagde API-call
 * gaan we weer op "online".
 */
import { View, StyleSheet } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { offlineQueue } from '@/services/offlineQueue';

export function OfflineIndicator() {
  const { isConnected, isLoading } = useNetworkStatus();
  const [queueSize, setQueueSize] = useState(0);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!isConnected) {
      // Update queue size when offline
      offlineQueue.getQueueSize().then(setQueueSize);
    } else {
      // Sync queue when online
      offlineQueue.sync(isConnected).then((result) => {
        if (result.synced > 0) {
          console.log(`[OfflineIndicator] Synced ${result.synced} items`);
        }
        offlineQueue.getQueueSize().then(setQueueSize);
      });
      // Technieken (en andere data) opnieuw ophalen na reconnect
      queryClient.invalidateQueries({ queryKey: ['techniques'] });
    }
  }, [isConnected, queryClient]);

  if (isLoading || isConnected) {
    return null;
  }

  return (
    <ThemedView style={styles.container}>
      <View style={styles.content}>
        <IconSymbol name="wifi.slash" size={16} color="#ef4444" />
        <ThemedText style={styles.text}>
          Offline – verbinding met backend niet geverifieerd
          {queueSize > 0 ? ` • ${queueSize} in wachtrij` : ''}
        </ThemedText>
      </View>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(239, 68, 68, 0.3)',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  text: {
    fontSize: 12,
    color: '#ef4444',
    fontWeight: '600',
  },
});
