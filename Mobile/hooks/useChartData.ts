/**
 * React hook for chart data processing
 */
import { useMemo } from 'react';
import type { SignalRecord } from '@/services/api/types';

export interface ChartDataPoint {
  x: number; // timestamp (ms)
  y: number; // value
}

export interface ChartData {
  data: ChartDataPoint[];
  min: number;
  max: number;
  avg: number;
}

export interface UseChartDataOptions {
  signals: SignalRecord[];
  signalType: 'ecg' | 'hr_derived' | 'resp_rr';
  timeWindow?: number; // milliseconds, default 30000 (30 seconds)
  maxPoints?: number; // maximum data points, default 300
}

export function useChartData(options: UseChartDataOptions): ChartData {
  const { signals, signalType, timeWindow = 30000, maxPoints = 300 } = options;

  return useMemo(() => {
    const now = Date.now();
    const cutoffTime = now - timeWindow;

    // Filter signals by type and time window
    const relevantSignals = signals
      .filter((s) => {
        if (s.signal !== signalType) return false;
        if (s.ts < cutoffTime) return false;
        return true;
      })
      .sort((a, b) => a.ts - b.ts) // Oldest first
      .slice(-maxPoints); // Keep only last maxPoints

    // Extract data points
    const dataPoints: ChartDataPoint[] = relevantSignals.map((signal) => {
      let y = 0;
      if (signalType === 'ecg' && signal.samples && signal.samples.length > 0) {
        // For ECG, use average of samples or first sample
        y = signal.samples[0] || 0;
      } else if (signalType === 'hr_derived' && signal.bpm !== undefined) {
        y = signal.bpm;
      } else if (signalType === 'resp_rr' && signal.estRR !== undefined) {
        y = signal.estRR;
      }

      return {
        x: signal.ts,
        y,
      };
    });

    // Calculate stats
    const values = dataPoints.map((p) => p.y).filter((v) => !isNaN(v) && isFinite(v));
    const min = values.length > 0 ? Math.min(...values) : 0;
    const max = values.length > 0 ? Math.max(...values) : 100;
    const avg = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;

    return {
      data: dataPoints,
      min,
      max,
      avg,
    };
  }, [signals, signalType, timeWindow, maxPoints]);
}
