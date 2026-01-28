/**
 * Respiratory Rate Chart Component
 * Line chart with target vs actual RR
 */
import { View, StyleSheet, Dimensions } from 'react-native';
import Svg, { Path, Line, Text as SvgText, G, Rect } from 'react-native-svg';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useChartData } from '@/hooks/useChartData';
import type { SignalRecord } from '@/services/api/types';

interface RRChartProps {
  signals: SignalRecord[];
  targetRR?: number;
  height?: number;
  showStats?: boolean;
}

const CHART_WIDTH = Dimensions.get('window').width - 32;
const CHART_HEIGHT = 150;
const PADDING = 20;

export function RRChart({
  signals,
  targetRR,
  height = CHART_HEIGHT,
  showStats = true,
}: RRChartProps) {
  const chartData = useChartData({
    signals,
    signalType: 'resp_rr',
    timeWindow: 60000, // 60 seconds
    maxPoints: 120,
  });

  const { data, min, max, avg } = chartData;

  // Calculate chart dimensions
  const chartWidth = CHART_WIDTH - PADDING * 2;
  const chartHeight = height - PADDING * 2;

  // Determine value range (include target if provided)
  const valueMin = targetRR !== undefined ? Math.min(min, targetRR - 2) : min;
  const valueMax = targetRR !== undefined ? Math.max(max, targetRR + 2) : max;
  const valueRange = valueMax - valueMin || 1;

  // Calculate scales
  const xScale = (timestamp: number): number => {
    if (data.length === 0) return PADDING;
    const timeRange = data[data.length - 1].x - data[0].x;
    if (timeRange === 0) return PADDING;
    const x = ((timestamp - data[0].x) / timeRange) * chartWidth + PADDING;
    return Math.max(PADDING, Math.min(CHART_WIDTH - PADDING, x));
  };

  const yScale = (value: number): number => {
    const y = ((value - valueMin) / valueRange) * chartHeight;
    return chartHeight - y + PADDING;
  };

  // Generate path for actual RR
  const generatePath = (): string => {
    if (data.length === 0) return '';

    let path = `M ${xScale(data[0].x)} ${yScale(data[0].y)}`;
    for (let i = 1; i < data.length; i++) {
      path += ` L ${xScale(data[i].x)} ${yScale(data[i].y)}`;
    }
    return path;
  };

  // Generate target line path
  const generateTargetPath = (): string => {
    if (!targetRR || data.length === 0) return '';
    const y = yScale(targetRR);
    return `M ${PADDING} ${y} L ${CHART_WIDTH - PADDING} ${y}`;
  };

  // Color zones based on target
  const getZoneColor = (value: number): string => {
    if (!targetRR) return 'rgba(59, 130, 246, 0.1)';
    const diff = Math.abs(value - targetRR);
    if (diff <= 1) return 'rgba(16, 185, 129, 0.1)'; // Green
    if (diff <= 2) return 'rgba(245, 158, 11, 0.1)'; // Orange
    return 'rgba(239, 68, 68, 0.1)'; // Red
  };

  // Y-axis labels
  const yLabels = [];
  const numLabels = 5;
  for (let i = 0; i <= numLabels; i++) {
    const value = valueMin + (valueRange * i) / numLabels;
    const y = PADDING + (chartHeight * (numLabels - i)) / numLabels;
    yLabels.push({ value: Math.round(value * 10) / 10, y });
  }

  if (data.length === 0) {
    return (
      <ThemedView style={[styles.container, { height }]}>
        <ThemedText type="subtitle" style={styles.title}>
          Ademhalingsfrequentie (BPM)
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
          Ademhalingsfrequentie (BPM)
        </ThemedText>
        {showStats && (
          <ThemedText style={styles.stats}>
            Avg: {avg.toFixed(1)} | Min: {min.toFixed(1)} | Max: {max.toFixed(1)}
            {targetRR && ` | Target: ${targetRR.toFixed(1)}`}
          </ThemedText>
        )}
      </View>
      <View style={styles.chartContainer}>
        <Svg width={CHART_WIDTH} height={height}>
          {/* Color zones background */}
          {targetRR && (
            <Rect
              x={PADDING}
              y={yScale(targetRR + 1)}
              width={chartWidth}
              height={yScale(targetRR - 1) - yScale(targetRR + 1)}
              fill="rgba(16, 185, 129, 0.1)"
            />
          )}

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
                  {label.value.toFixed(1)}
                </SvgText>
              </G>
            ))}
          </G>

          {/* Target line */}
          {targetRR && (
            <Path
              d={generateTargetPath()}
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              strokeDasharray="5,5"
            />
          )}

          {/* Actual RR line */}
          <Path
            d={generatePath()}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points with color coding */}
          {data.map((point, i) => {
            if (i % 10 !== 0) return null; // Show every 10th point
            const color = getZoneColor(point.y);
            return (
              <View
                key={i}
                style={[
                  styles.dataPoint,
                  {
                    left: xScale(point.x) - 3,
                    top: yScale(point.y) - 3,
                    backgroundColor: color.includes('green')
                      ? '#10b981'
                      : color.includes('orange')
                        ? '#f59e0b'
                        : '#ef4444',
                  },
                ]}
              />
            );
          })}
        </Svg>
      </View>
      {targetRR && (
        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#10b981' }]} />
            <ThemedText style={styles.legendText}>Target zone</ThemedText>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#3b82f6' }]} />
            <ThemedText style={styles.legendText}>Actual</ThemedText>
          </View>
        </View>
      )}
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
  },
  legend: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 8,
    paddingHorizontal: 4,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 2,
  },
  legendText: {
    fontSize: 11,
    opacity: 0.7,
  },
});
