/**
 * ECG Waveform Chart Component
 * Real-time ECG waveform visualization
 */
import { View, StyleSheet, Dimensions, ScrollView } from 'react-native';
import Svg, { Path, Line, G } from 'react-native-svg';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import type { SignalRecord } from '@/services/api/types';

interface ECGChartProps {
  signals: SignalRecord[];
  height?: number;
  timeWindow?: number; // milliseconds
}

const CHART_WIDTH = Dimensions.get('window').width - 32;
const CHART_HEIGHT = 200;
const PADDING = 20;
const DEFAULT_TIME_WINDOW = 10000; // 10 seconds

export function ECGChart({
  signals,
  height = CHART_HEIGHT,
  timeWindow = DEFAULT_TIME_WINDOW,
}: ECGChartProps) {
  // Filter ECG signals within time window
  const now = Date.now();
  const cutoffTime = now - timeWindow;

  const ecgSignals = signals
    .filter((s) => s.signal === 'ecg' && s.ts >= cutoffTime && s.samples && s.samples.length > 0)
    .sort((a, b) => a.ts - b.ts);

  // Flatten ECG samples into data points
  const dataPoints: Array<{ x: number; y: number }> = [];
  ecgSignals.forEach((signal) => {
    if (!signal.samples) return;
    const sampleInterval = 1000 / 130; // ~130 Hz sampling rate
    signal.samples.forEach((sample, index) => {
      dataPoints.push({
        x: signal.ts + index * sampleInterval,
        y: sample,
      });
    });
  });

  // Calculate chart dimensions
  const chartWidth = CHART_WIDTH - PADDING * 2;
  const chartHeight = height - PADDING * 2;

  // Calculate scales
  const xScale = (timestamp: number): number => {
    if (dataPoints.length === 0) return PADDING;
    const timeRange = dataPoints[dataPoints.length - 1].x - dataPoints[0].x;
    if (timeRange === 0) return PADDING;
    const x = ((timestamp - dataPoints[0].x) / timeRange) * chartWidth + PADDING;
    return Math.max(PADDING, Math.min(CHART_WIDTH - PADDING, x));
  };

  // Normalize ECG values (typically -2048 to 2048)
  const normalizeECG = (value: number): number => {
    // Normalize to -1 to 1 range, then scale to chart height
    const normalized = (value + 2048) / 4096; // Map -2048..2048 to 0..1
    return normalized * chartHeight;
  };

  const yScale = (value: number): number => {
    const y = normalizeECG(value);
    return chartHeight - y + PADDING;
  };

  // Generate path
  const generatePath = (): string => {
    if (dataPoints.length === 0) return '';

    // Sample data points for performance (show every Nth point)
    const sampleRate = Math.max(1, Math.floor(dataPoints.length / 500));
    const sampledPoints = dataPoints.filter((_, i) => i % sampleRate === 0);

    let path = `M ${xScale(sampledPoints[0].x)} ${yScale(sampledPoints[0].y)}`;
    for (let i = 1; i < sampledPoints.length; i++) {
      path += ` L ${xScale(sampledPoints[i].x)} ${yScale(sampledPoints[i].y)}`;
    }
    return path;
  };

  // Center line (baseline)
  const centerY = PADDING + chartHeight / 2;

  if (dataPoints.length === 0) {
    return (
      <ThemedView style={[styles.container, { height }]}>
        <ThemedText type="subtitle" style={styles.title}>
          ECG Waveform
        </ThemedText>
        <View style={styles.emptyContainer}>
          <ThemedText style={styles.emptyText}>Geen ECG data beschikbaar</ThemedText>
        </View>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={[styles.container, { height }]}>
      <ThemedText type="subtitle" style={styles.title}>
        ECG Waveform
      </ThemedText>
      <View style={styles.chartContainer}>
        <Svg width={CHART_WIDTH} height={height}>
          {/* Baseline */}
          <Line
            x1={PADDING}
            y1={centerY}
            x2={CHART_WIDTH - PADDING}
            y2={centerY}
            stroke="rgba(128, 128, 128, 0.3)"
            strokeWidth="1"
            strokeDasharray="2,2"
          />

          {/* ECG waveform */}
          <Path
            d={generatePath()}
            fill="none"
            stroke="#ef4444"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </Svg>
      </View>
      <ThemedText style={styles.info}>
        {dataPoints.length} samples | {(timeWindow / 1000).toFixed(1)}s window
      </ThemedText>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  title: {
    fontSize: 16,
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  chartContainer: {
    backgroundColor: 'rgba(128, 128, 128, 0.05)',
    borderRadius: 8,
    overflow: 'hidden',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyText: {
    opacity: 0.6,
    fontSize: 14,
  },
  info: {
    fontSize: 10,
    opacity: 0.6,
    marginTop: 4,
    paddingHorizontal: 4,
  },
});
