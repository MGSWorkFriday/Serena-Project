/**
 * Heart Rate Chart Component
 * Real-time BPM line chart
 */
import { View, StyleSheet, Dimensions } from 'react-native';
import Svg, { Path, Line, Text as SvgText, G } from 'react-native-svg';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useChartData, type ChartData } from '@/hooks/useChartData';
import type { SignalRecord } from '@/services/api/types';

interface HRChartProps {
  signals: SignalRecord[];
  height?: number;
  showStats?: boolean;
}

const CHART_WIDTH = Dimensions.get('window').width - 32;
const CHART_HEIGHT = 150;
const PADDING = 20;

export function HRChart({ signals, height = CHART_HEIGHT, showStats = true }: HRChartProps) {
  const chartData = useChartData({
    signals,
    signalType: 'hr_derived',
    timeWindow: 60000, // 60 seconds
    maxPoints: 120,
  });

  const { data, min, max, avg } = chartData;

  // Calculate chart dimensions
  const chartWidth = CHART_WIDTH - PADDING * 2;
  const chartHeight = height - PADDING * 2;

  // Calculate scales
  const xScale = (timestamp: number): number => {
    if (data.length === 0) return PADDING;
    const timeRange = data[data.length - 1].x - data[0].x;
    if (timeRange === 0) return PADDING;
    const x = ((timestamp - data[0].x) / timeRange) * chartWidth + PADDING;
    return Math.max(PADDING, Math.min(CHART_WIDTH - PADDING, x));
  };

  const yScale = (value: number): number => {
    const valueRange = max - min || 1;
    const y = ((value - min) / valueRange) * chartHeight;
    return chartHeight - y + PADDING;
  };

  // Generate path
  const generatePath = (): string => {
    if (data.length === 0) return '';

    let path = `M ${xScale(data[0].x)} ${yScale(data[0].y)}`;
    for (let i = 1; i < data.length; i++) {
      path += ` L ${xScale(data[i].x)} ${yScale(data[i].y)}`;
    }
    return path;
  };

  // Y-axis labels
  const yLabels = [];
  const numLabels = 5;
  for (let i = 0; i <= numLabels; i++) {
    const value = min + ((max - min) * i) / numLabels;
    const y = PADDING + (chartHeight * (numLabels - i)) / numLabels;
    yLabels.push({ value: Math.round(value), y });
  }

  if (data.length === 0) {
    return (
      <ThemedView style={[styles.container, { height }]}>
        <ThemedText type="subtitle" style={styles.title}>
          Hartslag (BPM)
        </ThemedText>
        <View style={styles.emptyContainer}>
          <ThemedText style={styles.emptyText}>Geen data beschikbaar</ThemedText>
        </View>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={[styles.container, { height }]}>
      <View style={styles.header}>
        <ThemedText type="subtitle" style={styles.title}>
          Hartslag (BPM)
        </ThemedText>
        {showStats && (
          <ThemedText style={styles.stats}>
            Avg: {Math.round(avg)} | Min: {Math.round(min)} | Max: {Math.round(max)}
          </ThemedText>
        )}
      </View>
      <View style={styles.chartContainer}>
        <Svg width={CHART_WIDTH} height={height}>
          {/* Y-axis labels */}
          <G>
            {yLabels.map((label, i) => (
              <G key={i}>
                <Line
                  x1={PADDING}
                  y1={label.y}
                  x2={CHART_WIDTH - PADDING}
                  y2={label.y}
                  stroke="rgba(128, 128, 128, 0.2)"
                  strokeWidth="1"
                />
                <SvgText
                  x={PADDING - 5}
                  y={label.y + 4}
                  fontSize="10"
                  fill="#9ca3af"
                  textAnchor="end">
                  {label.value}
                </SvgText>
              </G>
            ))}
          </G>

          {/* Chart line */}
          <Path
            d={generatePath()}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {data.map((point, i) => {
            if (i % 10 !== 0) return null; // Show every 10th point
            return (
              <View
                key={i}
                style={[
                  styles.dataPoint,
                  {
                    left: xScale(point.x) - 3,
                    top: yScale(point.y) - 3,
                  },
                ]}
              />
            );
          })}
        </Svg>
      </View>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  title: {
    fontSize: 16,
  },
  stats: {
    fontSize: 11,
    opacity: 0.7,
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
  dataPoint: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#3b82f6',
  },
});
