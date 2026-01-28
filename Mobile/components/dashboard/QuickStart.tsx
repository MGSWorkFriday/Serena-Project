/**
 * Quick Start Component
 * Button to quickly start a new session
 */
import { View, StyleSheet, TouchableOpacity, Alert, Platform } from 'react-native';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { router } from 'expo-router';
import { useBluetooth } from '@/hooks/useBluetooth';
import { useActiveSession, useEndSession } from '@/hooks/useSessions';

export function QuickStart() {
  const { connected, deviceId } = useBluetooth();
  const { data: activeSession } = useActiveSession(deviceId || undefined);
  const endSessionMutation = useEndSession();

  const handlePress = () => {
    if (activeSession) {
      router.push('/session');
    } else if (connected && deviceId) {
      router.push('/techniques');
    } else {
      router.push('/device');
    }
  };

  const handleSaveSession = () => {
    const sid = activeSession?.session_id;
    if (!sid) return;
    const msg =
      'Weet je zeker dat je de sessie wilt bewaren en afsluiten? De sessie wordt opgeslagen als voltooid. Start daarna een nieuwe sessie om verder te gaan.';
    if (Platform.OS === 'web') {
      if (!window.confirm(msg)) return;
      endSessionMutation.mutateAsync(sid).catch(() => {
        window.alert('Kon sessie niet bewaren');
      });
      return;
    }
    Alert.alert('Sessie bewaren', msg, [
      { text: 'Annuleren', style: 'cancel' },
      {
        text: 'Bewaren',
        onPress: async () => {
          try {
            await endSessionMutation.mutateAsync(sid);
          } catch {
            Alert.alert('Fout', 'Kon sessie niet bewaren');
          }
        },
      },
    ]);
  };

  const getButtonText = () => {
    if (activeSession) return 'Ga door met sessie';
    if (connected && deviceId) return 'Start nieuwe sessie';
    return 'Verbind device eerst';
  };

  const isDisabled = !connected || !deviceId;
  const canTapToDevice = getButtonText() === 'Verbind device eerst';

  return (
    <View style={styles.wrapper}>
      <TouchableOpacity
        onPress={handlePress}
        disabled={!canTapToDevice && isDisabled && !activeSession}
        activeOpacity={0.7}
        style={[styles.button, !canTapToDevice && isDisabled && !activeSession && styles.buttonDisabled]}>
        <View style={styles.buttonContent}>
          <IconSymbol
            name={activeSession ? 'play.circle.fill' : 'play.fill'}
            size={32}
            color="#fff"
          />
          <ThemedText type="title" style={styles.buttonText}>
            {getButtonText()}
          </ThemedText>
        </View>
        {activeSession && (
          <ThemedText style={styles.activeSession}>
            Actieve sessie aan het lopen...
          </ThemedText>
        )}
      </TouchableOpacity>
      {activeSession && (
        <TouchableOpacity
          onPress={handleSaveSession}
          disabled={endSessionMutation.isPending}
          style={[styles.saveButton, endSessionMutation.isPending && styles.saveButtonDisabled]}
          activeOpacity={0.7}>
          <IconSymbol name="square.and.arrow.down.fill" size={20} color="#fff" />
          <ThemedText style={styles.saveButtonText}>
            {endSessionMutation.isPending ? 'Bewaren…' : 'Bewaar sessie'}
          </ThemedText>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#10b981',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  buttonDisabled: {
    backgroundColor: '#6b7280',
    opacity: 0.6,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  buttonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '600',
  },
  activeSession: {
    marginTop: 8,
    fontSize: 12,
    color: '#fff',
    opacity: 0.9,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 14,
    borderRadius: 12,
    backgroundColor: '#10b981',
    marginTop: 10,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
});
