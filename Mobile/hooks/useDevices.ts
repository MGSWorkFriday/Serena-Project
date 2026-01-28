/**
 * React hook for device management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { Device, DeviceCreate, DeviceUpdate } from '@/services/api/types';

export function useDevices() {
  return useQuery({
    queryKey: ['devices'],
    queryFn: () => apiClient.getDevices(),
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useDevice(deviceId: string | null) {
  return useQuery({
    queryKey: ['devices', deviceId],
    queryFn: () => {
      if (!deviceId) throw new Error('Device ID required');
      return apiClient.getDevice(deviceId);
    },
    enabled: !!deviceId,
    staleTime: 30 * 1000,
  });
}

export function useCreateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DeviceCreate) => apiClient.createDevice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });
}

export function useUpdateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: string; data: DeviceUpdate }) =>
      apiClient.updateDevice(deviceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['devices', variables.deviceId] });
    },
  });
}
