/**
 * React hook for parameter sets management
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { ParameterSet } from '@/services/api/types';

export function useParameterSets() {
  return useQuery({
    queryKey: ['parameterSets'],
    queryFn: () => apiClient.getParameterSets(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useParameterSet(version: string | null) {
  return useQuery({
    queryKey: ['parameterSets', version],
    queryFn: () => {
      if (!version) throw new Error('Parameter version required');
      return apiClient.getParameterSet(version);
    },
    enabled: !!version,
    staleTime: 5 * 60 * 1000,
  });
}
