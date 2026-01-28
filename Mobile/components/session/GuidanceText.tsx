/**
 * Guidance Text Component
 * Shows color-coded feedback text
 */
import { View, Text, StyleSheet } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';

interface GuidanceTextProps {
  text?: string;
  audioText?: string;
  color?: 'ok' | 'warn' | 'bad' | 'accent';
}

const colorMap = {
  ok: '#10b981', // Green
  warn: '#f59e0b', // Orange
  bad: '#ef4444', // Red
  accent: '#3b82f6', // Blue
};

export function GuidanceText({ text, audioText, color = 'ok' }: GuidanceTextProps) {
  if (!text && !audioText) {
    return (
      <ThemedView style={styles.container}>
        <ThemedText style={styles.placeholder}>Wacht op feedback...</ThemedText>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={[styles.container, { borderLeftColor: colorMap[color] }]}>
      {text && (
        <ThemedText type="subtitle" style={[styles.text, { color: colorMap[color] }]}>
          {text}
        </ThemedText>
      )}
      {audioText && text !== audioText && (
        <ThemedText style={styles.audioText}>{audioText}</ThemedText>
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderLeftWidth: 4,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
  },
  text: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  audioText: {
    fontSize: 14,
    opacity: 0.8,
    marginTop: 4,
  },
  placeholder: {
    textAlign: 'center',
    opacity: 0.6,
    fontSize: 14,
  },
});
