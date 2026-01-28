/**
 * React hook for feedback rules management
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { FeedbackRules } from '@/services/api/types';

export function useFeedbackRules() {
  return useQuery({
    queryKey: ['feedbackRules'],
    queryFn: () => apiClient.getFeedbackRules(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
