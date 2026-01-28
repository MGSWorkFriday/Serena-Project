/**
 * Network status: "Offline" betekent dat de periodieke ping naar de backend (GET /api/v1/ping)
 * is mislukt. Andere API-calls (technieken, sessies, …) kunnen wél slagen – bijv. als de
 * backend net opstartte toen de ping liep. Bij een geslaagde API-call zetten we ons weer
 * op "online".
 */
import { useState, useEffect } from 'react';
import { apiClient } from '@/services/api';
import { apiSuccess } from '@/services/api/apiSuccess';

export interface NetworkStatus {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: string | null;
}

export function useNetworkStatus(): NetworkStatus & { isLoading: boolean } {
  const [status, setStatus] = useState<NetworkStatus>({
    isConnected: true,
    isInternetReachable: true,
    type: null,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Bij een geslaagde API-call (technieken, status, …) weer "online" zetten
  useEffect(() => {
    const off = apiSuccess.on(() => {
      setStatus((s) => (s.isConnected ? s : { ...s, isConnected: true, isInternetReachable: true, type: 'unknown' }));
      setIsLoading(false);
    });
    return off;
  }, []);

  // Periodieke ping naar GET /api/v1/ping (geen DB, alleen bereikbaarheid)
  useEffect(() => {
    let mounted = true;

    const delays = [0, 800, 2000, 4000];
    const checkStatus = async (attempt = 0) => {
      try {
        await apiClient.getPing();
        if (mounted) {
          setStatus({ isConnected: true, isInternetReachable: true, type: 'unknown' });
          setIsLoading(false);
        }
      } catch (e) {
        const next = attempt + 1;
        if (next < delays.length && mounted) {
          setTimeout(() => checkStatus(next), delays[next]);
          return;
        }
        if (mounted) {
          setStatus({ isConnected: false, isInternetReachable: false, type: null });
          setIsLoading(false);
          if (__DEV__) {
            console.log('[useNetworkStatus] Ping mislukt (GET /api/v1/ping), Offline');
          }
        }
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return {
    ...status,
    isLoading,
  };
}
