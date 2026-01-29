/**
 * Active Session Screen
 * Shows real-time breathing exercise with breathing ball animation
 */
import { View, StyleSheet, ScrollView, TouchableOpacity, Alert, Platform } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { BreathingBall } from '@/components/session/BreathingBall';
import { StatsCards } from '@/components/session/StatsCards';
import { GuidanceText } from '@/components/session/GuidanceText';
import { HRChart } from '@/components/charts/HRChart';
import { RRChart } from '@/components/charts/RRChart';
import { ECGChart } from '@/components/charts/ECGChart';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useSessionState } from '@/hooks/useSession';
import { useSignalStream } from '@/hooks/useSignalStream';
import { useBluetooth } from '@/hooks/useBluetooth';
import { useECGIngest } from '@/hooks/useECGIngest';
import { router, useLocalSearchParams } from 'expo-router';
import { useState, useEffect } from 'react';
import { audioService } from '@/services/audio/audioService';

export default function SessionScreen() {
  const params = useLocalSearchParams<{ sessionId?: string }>();
  const { session, heartRate, actualRR, targetRR, latestGuidance, endSession, isLoading, isEnding } =
    useSessionState(params.sessionId);
  const { deviceId, connected } = useBluetooth();
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [showCharts, setShowCharts] = useState(false);

  // Send Polar ECG to backend when session is active; backend computes BPM and heart rate
  useECGIngest({
    sessionId: session?.session_id ?? null,
    deviceId: session?.device_id ?? deviceId ?? null,
    enabled: !!(session && session.status === 'active' && (session.device_id || deviceId) && connected),
  });

  // Get real-time signals for charts
  const { signals: chartSignals } = useSignalStream({
    deviceId: deviceId || undefined,
    signalTypes: ['ecg', 'hr_derived', 'resp_rr'],
    enabled: !!session && session.status === 'active' && showCharts,
  });

  // Handle audio feedback
  useEffect(() => {
    audioService.setEnabled(audioEnabled);
  }, [audioEnabled]);

  // Close session when browser/tab is closed (web only)
  useEffect(() => {
    if (Platform.OS !== 'web' || !session?.session_id) return;

    const handleBeforeUnload = () => {
      // Use fetch with keepalive for reliable session close on page unload
      const url = `${process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sessions/${session.session_id}/end`;
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
        keepalive: true,
      }).catch(() => {});
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [session?.session_id]);

  useEffect(() => {
    if (latestGuidance?.audioText && audioEnabled) {
      audioService.speak(latestGuidance.audioText);
    }
  }, [latestGuidance?.audioText, audioEnabled]);

  const handleSaveSession = () => {
    const msg =
      'Weet je zeker dat je de sessie wilt bewaren en afsluiten? De sessie wordt opgeslagen als voltooid. Start daarna een nieuwe sessie om verder te gaan.';
    const run = async () => {
      try {
        await endSession();
        router.back();
      } catch {
        if (Platform.OS === 'web') window.alert('Kon sessie niet bewaren');
        else Alert.alert('Fout', 'Kon sessie niet bewaren');
      }
    };
    if (Platform.OS === 'web') {
      if (window.confirm(msg)) run();
      return;
    }
    Alert.alert('Sessie bewaren', msg, [
      { text: 'Annuleren', style: 'cancel' },
      { text: 'Bewaren', onPress: run },
    ]);
  };

  const handleTechniqueInfo = () => {
    if (session?.technique_name) {
      // TODO: Navigate to technique detail
      Alert.alert('Techniek', session.technique_name);
    }
  };

  // Get breath cycle from session metadata protocol
  // Protocol format: [[in, hold1, out, hold2, repeats], ...] - use first step
  const protocol = (session?.metadata as any)?.protocol;
  const breathCycle = (() => {
    console.log('[Session] Raw protocol from metadata:', JSON.stringify(protocol));
    if (protocol && Array.isArray(protocol) && protocol.length > 0) {
      const step = protocol[0]; // Use first step
      console.log('[Session] First step:', JSON.stringify(step));
      if (Array.isArray(step) && step.length >= 4) {
        const cycle = {
          in: step[0] || 4,
          hold1: step[1] || 0,
          out: step[2] || 4,
          hold2: step[3] || 0,
        };
        console.log('[Session] Extracted breathCycle:', JSON.stringify(cycle));
        return cycle;
      }
    }
    console.log('[Session] Using default breathCycle');
    // Default fallback
    return { in: 4, out: 4, hold1: 0, hold2: 0 };
  })();

  if (isLoading) {
    return (
      <ThemedView style={styles.container}>
        <ThemedText>Laden...</ThemedText>
      </ThemedView>
    );
  }

  if (!session) {
    return (
      <ThemedView style={styles.container}>
        <ThemedText type="title">Geen actieve sessie</ThemedText>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ThemedText>Terug</ThemedText>
        </TouchableOpacity>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <IconSymbol name="chevron.left" size={24} color="#fff" />
          </TouchableOpacity>
          <ThemedText type="subtitle" style={styles.headerTitle}>
            {session.technique_name || 'Ademhalingsoefening'}
          </ThemedText>
          <TouchableOpacity onPress={handleTechniqueInfo} style={styles.infoButton}>
            <IconSymbol name="info.circle" size={24} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Breathing Ball */}
        <View style={styles.ballContainer}>
          <BreathingBall breathCycle={breathCycle} size={280} color="#3498db" />
        </View>

        {/* Stats Cards */}
        <StatsCards heartRate={heartRate} actualRR={actualRR} targetRR={targetRR} />

        {/* Guidance Text */}
        <GuidanceText
          text={latestGuidance?.text}
          audioText={latestGuidance?.audioText}
          color={latestGuidance?.color}
        />

        {/* Charts Toggle */}
        <TouchableOpacity
          onPress={() => setShowCharts(!showCharts)}
          style={styles.chartsToggle}>
          <IconSymbol
            name={showCharts ? 'chart.line.uptrend.xyaxis' : 'chart.line.uptrend.xyaxis'}
            size={20}
            color="#fff"
          />
          <ThemedText style={styles.chartsToggleText}>
            {showCharts ? 'Verberg grafieken' : 'Toon grafieken'}
          </ThemedText>
        </TouchableOpacity>

        {/* Charts */}
        {showCharts && (
          <View style={styles.chartsContainer}>
            <HRChart signals={chartSignals} />
            <RRChart signals={chartSignals} targetRR={targetRR} />
            <ECGChart signals={chartSignals} />
          </View>
        )}

        {/* Controls */}
        <View style={styles.controls}>
          <TouchableOpacity
            onPress={() => setAudioEnabled(!audioEnabled)}
            style={[styles.controlButton, !audioEnabled && styles.controlButtonDisabled]}>
            <IconSymbol
              name={audioEnabled ? 'speaker.wave.2.fill' : 'speaker.slash.fill'}
              size={24}
              color="#fff"
            />
            <ThemedText style={styles.controlText}>
              {audioEnabled ? 'Audio aan' : 'Audio uit'}
            </ThemedText>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleSaveSession}
            disabled={isEnding}
            style={[styles.controlButton, styles.saveButton, isEnding && styles.controlButtonDisabled]}
            accessibilityLabel="Bewaar sessie"
            accessibilityRole="button">
            <IconSymbol name="square.and.arrow.down.fill" size={24} color="#fff" />
            <ThemedText style={styles.controlText}>{isEnding ? 'Bewaren…' : 'Bewaar sessie'}</ThemedText>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 18,
  },
  infoButton: {
    padding: 8,
  },
  ballContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 300,
    marginBottom: 24,
  },
  controls: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  controlButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#3b82f6',
  },
  controlButtonDisabled: {
    backgroundColor: '#6b7280',
    opacity: 0.6,
  },
  saveButton: {
    backgroundColor: '#10b981',
  },
  controlText: {
    color: '#fff',
    fontWeight: '600',
  },
  chartsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    marginTop: 16,
    marginBottom: 8,
  },
  chartsToggleText: {
    color: '#3b82f6',
    fontWeight: '600',
    fontSize: 14,
  },
  chartsContainer: {
    marginTop: 8,
    marginBottom: 16,
  },
});
