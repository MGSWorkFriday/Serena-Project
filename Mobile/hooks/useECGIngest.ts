/**
 * Sends Polar ECG stream to the backend when a session is active.
 * Backend runs resp_rr_estimator and returns resp_rr (BPM) and hr_derived (heart rate)
 * which are shown via useSignalStream / useLatestHR / useLatestRR.
 */
import { useEffect, useRef } from 'react';
import { useBluetooth } from '@/hooks/useBluetooth';
import { apiClient } from '@/services/api';
import type { RecordIngest } from '@/services/api/types';

export interface UseECGIngestOptions {
  sessionId: string | null;
  deviceId: string | null;
  enabled: boolean;
}

export function useECGIngest(options: UseECGIngestOptions): void {
  const { sessionId, deviceId, enabled } = options;
  const { subscribeECG, connected } = useBluetooth();
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;

  // Debug: log current state
  console.log('[useECGIngest] State:', { sessionId, deviceId, enabled, connected });

  useEffect(() => {
    if (!enabled || !sessionId || !deviceId || !connected) {
      console.log('[useECGIngest] Not starting - missing:', {
        enabled,
        hasSessionId: !!sessionId,
        hasDeviceId: !!deviceId,
        connected,
      });
      return;
    }
    console.log('[useECGIngest] Starting ECG subscription...');

    const onECGData = (data: { timestamp: number; samples: number[] }) => {
      if (!enabledRef.current || !data.samples?.length) return;

      console.log('[useECGIngest] ECG data received, samples:', data.samples.length);

      const record: RecordIngest = {
        device_id: deviceId,
        session_id: sessionId,
        signal: 'ecg',
        ts: data.timestamp,
        samples: data.samples,
      };

      apiClient.ingestRecords([record]).catch((err) => {
        console.warn('[ECG Ingest] Error sending:', err?.message || err);
      });
    };

    let mounted = true;
    console.log('[useECGIngest] Calling subscribeECG...');
    subscribeECG(onECGData)
      .then(() => console.log('[useECGIngest] subscribeECG success!'))
      .catch((err) => {
        console.error('[useECGIngest] subscribeECG FAILED:', err);
      });

    return () => {
      mounted = false;
      enabledRef.current = false;
    };
  }, [enabled, sessionId, deviceId, connected, subscribeECG]);
}
