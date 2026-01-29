/**
 * React hook for session management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { Session, SessionCreate, SessionUpdate } from '@/services/api/types';

export interface UseSessionsOptions {
  deviceId?: string;
  status?: 'active' | 'completed' | 'cancelled';
}

export function useSessions(options?: UseSessionsOptions) {
  const { deviceId, status } = options || {};
  return useQuery({
    queryKey: ['sessions', deviceId, status],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (deviceId) params.device_id = deviceId;
      if (status) params.status = status;
      return apiClient.getSessions(Object.keys(params).length > 0 ? params : undefined);
    },
    staleTime: 10 * 1000, // 10 seconds
  });
}

export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: ['sessions', sessionId],
    queryFn: () => {
      if (!sessionId) throw new Error('Session ID required');
      return apiClient.getSession(sessionId);
    },
    enabled: !!sessionId,
    staleTime: 5 * 1000,
  });
}

export function useActiveSession(deviceId?: string) {
  return useQuery({
    queryKey: ['sessions', 'active', deviceId],
    queryFn: async () => {
      const sessions = await apiClient.getSessions(deviceId ? { device_id: deviceId } : undefined);
      return sessions.find((s) => s.status === 'active') || null;
    },
    staleTime: 5 * 1000,
    refetchInterval: 5 * 1000, // Poll every 5 seconds for active session
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SessionCreate) => apiClient.createSession(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['sessions', 'active', variables.device_id] });
    },
  });
}

export function useEndSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => apiClient.endSession(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['sessions', sessionId] });
      // Zorg dat actieve-sessie-queries direct refetchen, zodat "Ga door met sessie" / "Bewaar sessie"
      // verdwijnen en "Start nieuwe sessie" getoond wordt
      queryClient.invalidateQueries({ queryKey: ['sessions', 'active'] });
    },
  });
}
