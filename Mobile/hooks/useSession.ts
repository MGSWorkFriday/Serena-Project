/**
 * React hook for active session management
 */
import { useEffect, useState } from 'react';
import { useSession, useActiveSession, useEndSession } from './useSessions';
import { useSignalStream } from './useSignalStream';
import { useBluetooth } from './useBluetooth';
import { useLatestHR, useLatestRR } from './useRecentSignals';
import type { Session } from '@/services/api/types';

export interface UseSessionReturn {
  session: Session | null;
  isLoading: boolean;
  error: Error | null;
  heartRate?: number;
  actualRR?: number;
  targetRR?: number;
  latestGuidance?: {
    text?: string;
    audioText?: string;
    color?: 'ok' | 'warn' | 'bad' | 'accent';
  };
  endSession: () => Promise<void>;
  isEnding: boolean;
}

export function useSessionState(sessionId?: string): UseSessionReturn {
  const { deviceId } = useBluetooth();
  const { data: activeSession } = useActiveSession(deviceId || undefined);
  const { data: session, isLoading, error } = useSession(sessionId || activeSession?.session_id || null);
  const endSessionMutation = useEndSession();

  // Polling fallback for HR and RR
  const { bpm: bpmPolled } = useLatestHR(deviceId || undefined);
  const { estRR: estRRPolled } = useLatestRR(deviceId || undefined);

  // Stream real-time signals (BPM, HR, guidance from backend)
  const { getLatestSignal } = useSignalStream({
    deviceId: deviceId || undefined,
    signalTypes: ['guidance', 'resp_rr', 'hr_derived'],
    enabled: !!session && session.status === 'active',
  });

  // Prefer stream data for real-time display; fall back to polling
  const hrSignal = getLatestSignal('hr_derived');
  const rrSignal = getLatestSignal('resp_rr');
  
  // Debug logging
  if (rrSignal) {
    console.log('[useSession] resp_rr signal:', JSON.stringify(rrSignal));
  }
  console.log('[useSession] estRRPolled:', estRRPolled);
  
  const heartRate = hrSignal?.bpm ?? bpmPolled;
  const actualRR = rrSignal?.estRR ?? estRRPolled;

  // Get latest guidance
  const latestGuidanceSignal = getLatestSignal('guidance');
  const latestGuidance = latestGuidanceSignal
    ? {
        text: latestGuidanceSignal.text,
        audioText: latestGuidanceSignal.audio_text,
        color: latestGuidanceSignal.color,
      }
    : undefined;

  const endSession = async () => {
    if (session?.session_id) {
      await endSessionMutation.mutateAsync(session.session_id);
    }
  };

  return {
    session: session || null,
    isLoading,
    error: error as Error | null,
    heartRate,
    actualRR,
    targetRR: session?.target_rr,
    latestGuidance,
    endSession,
    isEnding: endSessionMutation.isPending,
  };
}
