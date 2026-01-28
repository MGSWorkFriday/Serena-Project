/**
 * Unit Tests for useChartData Hook
 */
import { renderHook } from '@testing-library/react-native';
import { useChartData } from '@/hooks/useChartData';
import type { SignalRecord, SignalType } from '@/services/api/types';

describe('useChartData Hook', () => {
  const createSignal = (
    ts: number,
    signal: SignalType,
    value?: number
  ): SignalRecord => ({
    ts,
    signal,
    device_id: 'test-device',
    session_id: 'test-session',
    ...(value !== undefined && signal === 'hr_derived' ? { bpm: value } : {}),
    ...(value !== undefined && signal === 'resp_rr' ? { estRR: value } : {}),
  });

  it('should filter signals by type', () => {
    const signals: SignalRecord[] = [
      createSignal(1000, 'hr_derived', 70),
      createSignal(2000, 'hr_derived', 75),
      createSignal(3000, 'resp_rr', 6),
    ];

    const { result } = renderHook(() =>
      useChartData({
        signals,
        signalType: 'hr_derived',
        timeWindow: 10000,
        maxPoints: 100,
      })
    );

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data[0].y).toBe(70);
    expect(result.current.data[1].y).toBe(75);
  });

  it('should filter by time window', () => {
    const now = Date.now();
    const signals: SignalRecord[] = [
      createSignal(now - 5000, 'hr_derived', 70), // Within window
      createSignal(now - 40000, 'hr_derived', 75), // Outside window
      createSignal(now - 2000, 'hr_derived', 80), // Within window
    ];

    const { result } = renderHook(() =>
      useChartData({
        signals,
        signalType: 'hr_derived',
        timeWindow: 30000, // 30 seconds
        maxPoints: 100,
      })
    );

    expect(result.current.data).toHaveLength(2);
  });

  it('should limit data points', () => {
    const signals: SignalRecord[] = Array.from({ length: 200 }, (_, i) =>
      createSignal(1000 + i * 100, 'hr_derived', 70 + i)
    );

    const { result } = renderHook(() =>
      useChartData({
        signals,
        signalType: 'hr_derived',
        timeWindow: 100000,
        maxPoints: 50,
      })
    );

    expect(result.current.data.length).toBeLessThanOrEqual(50);
  });

  it('should calculate min, max, and avg', () => {
    const signals: SignalRecord[] = [
      createSignal(1000, 'hr_derived', 60),
      createSignal(2000, 'hr_derived', 70),
      createSignal(3000, 'hr_derived', 80),
    ];

    const { result } = renderHook(() =>
      useChartData({
        signals,
        signalType: 'hr_derived',
        timeWindow: 10000,
        maxPoints: 100,
      })
    );

    expect(result.current.min).toBe(60);
    expect(result.current.max).toBe(80);
    expect(result.current.avg).toBeCloseTo(70, 1);
  });

  it('should handle empty signals', () => {
    const { result } = renderHook(() =>
      useChartData({
        signals: [],
        signalType: 'hr_derived',
        timeWindow: 10000,
        maxPoints: 100,
      })
    );

    expect(result.current.data).toHaveLength(0);
    expect(result.current.min).toBe(0);
    expect(result.current.max).toBe(0);
    expect(result.current.avg).toBe(0);
  });
});
