/**
 * Home/Dashboard Screen
 * Main screen with overview and quick actions
 */
import { ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { DeviceCard } from '@/components/dashboard/DeviceCard';
import { QuickStart } from '@/components/dashboard/QuickStart';
import { CurrentStats } from '@/components/dashboard/CurrentStats';
import { RecentSessions } from '@/components/dashboard/RecentSessions';
import { useBluetooth } from '@/hooks/useBluetooth';
import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export default function HomeScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const queryClient = useQueryClient();
  const { initialize } = useBluetooth();

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      // Refresh all queries
      await queryClient.invalidateQueries();
      // Reinitialize Bluetooth if needed
      await initialize();
    } catch (error) {
      console.error('Refresh error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <ThemedView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        <ThemedView style={styles.header}>
          <ThemedText type="title">Serena</ThemedText>
          <ThemedText style={styles.subtitle}>Ademhalingsoefeningen</ThemedText>
        </ThemedView>

        <DeviceCard />
        <QuickStart />
        <CurrentStats />
        <RecentSessions />
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 24,
    alignItems: 'center',
  },
  subtitle: {
    fontSize: 16,
    opacity: 0.7,
    marginTop: 4,
  },
});
