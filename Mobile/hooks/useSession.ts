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

  // Get latest signals
  const { bpm } = useLatestHR(deviceId || undefined);
  const { estRR } = useLatestRR(deviceId || undefined);

  // Stream real-time signals
  const { getLatestSignal } = useSignalStream({
    deviceId: deviceId || undefined,
    signalTypes: ['guidance', 'resp_rr', 'hr_derived'],
    enabled: !!session && session.status === 'active',
  });

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
    heartRate: bpm,
    actualRR: estRR,
    targetRR: session?.target_rr,
    latestGuidance,
    endSession,
    isEnding: endSessionMutation.isPending,
  };
}
