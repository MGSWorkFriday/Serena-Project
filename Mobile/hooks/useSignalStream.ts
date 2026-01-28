/**
 * React hook for real-time signal streaming via SSE
 */
import { useEffect, useRef, useState } from 'react';
import { createSSEStream, SSEClient } from '@/services/api';
import type { SignalRecord, SignalType } from '@/services/api/types';

export interface UseSignalStreamOptions {
  deviceId?: string;
  signalTypes?: SignalType[];
  enabled?: boolean;
}

export function useSignalStream(options: UseSignalStreamOptions = {}) {
  const { deviceId, signalTypes, enabled = true } = options;
  const [signals, setSignals] = useState<SignalRecord[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sseClientRef = useRef<SSEClient | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Create SSE client
    const client = createSSEStream({
      deviceId,
      signalTypes,
      onMessage: (signal) => {
        setSignals((prev) => {
          // Keep only last 1000 signals to prevent memory issues
          const updated = [signal, ...prev].slice(0, 1000);
          return updated;
        });
      },
      onOpen: () => {
        setIsConnected(true);
        setError(null);
      },
      onError: (err) => {
        setError(err.message);
        setIsConnected(false);
      },
      onClose: () => {
        setIsConnected(false);
      },
    });

    sseClientRef.current = client;
    client.connect();

    // Cleanup on unmount
    return () => {
      client.close();
      sseClientRef.current = null;
    };
  }, [deviceId, enabled, signalTypes?.join(',')]);

  // Get latest signal of specific type
  const getLatestSignal = (signalType: SignalType): SignalRecord | null => {
    return signals.find((s) => s.signal === signalType) || null;
  };

  // Get all signals of specific type
  const getSignalsByType = (signalType: SignalType): SignalRecord[] => {
    return signals.filter((s) => s.signal === signalType);
  };

  return {
    signals,
    isConnected,
    error,
    getLatestSignal,
    getSignalsByType,
  };
}
