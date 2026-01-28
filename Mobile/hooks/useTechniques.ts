/**
 * React hook for technique management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { Technique, TechniqueCreate } from '@/services/api/types';

export function useTechniques(publicOnly = true) {
  return useQuery({
    queryKey: ['techniques', publicOnly],
    queryFn: () => apiClient.getTechniques(publicOnly),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useTechnique(name: string | null) {
  return useQuery({
    queryKey: ['techniques', name],
    queryFn: () => {
      if (!name) throw new Error('Technique name required');
      return apiClient.getTechnique(name);
    },
    enabled: !!name,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateTechnique() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TechniqueCreate) => apiClient.createOrUpdateTechnique(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['techniques'] });
    },
  });
}

export function useDeleteTechnique() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => apiClient.deleteTechnique(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['techniques'] });
    },
  });
}
