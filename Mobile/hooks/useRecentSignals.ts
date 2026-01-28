/**
 * React hook for recent signal data
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { SignalRecord } from '@/services/api/types';

export function useRecentSignals(deviceId?: string, limit = 100) {
  return useQuery({
    queryKey: ['signals', 'recent', deviceId, limit],
    queryFn: () => apiClient.getRecentSignals(deviceId, limit),
    staleTime: 5 * 1000, // 5 seconds
    refetchInterval: 5 * 1000, // Poll every 5 seconds
  });
}

export function useLatestHR(deviceId?: string) {
  const { data: signals } = useRecentSignals(deviceId, 50);

  const list = Array.isArray(signals) ? signals : [];
  const latestHR = list
    .filter((s) => s.signal === 'hr_derived')
    .sort((a, b) => b.ts - a.ts)[0];

  return {
    bpm: latestHR?.bpm,
    timestamp: latestHR?.ts,
    signal: latestHR,
  };
}

export function useLatestRR(deviceId?: string) {
  const { data: signals } = useRecentSignals(deviceId, 50);

  const list = Array.isArray(signals) ? signals : [];
  const latestRR = list
    .filter((s) => s.signal === 'resp_rr')
    .sort((a, b) => b.ts - a.ts)[0];

  return {
    estRR: latestRR?.estRR,
    timestamp: latestRR?.ts,
    signal: latestRR,
  };
}
