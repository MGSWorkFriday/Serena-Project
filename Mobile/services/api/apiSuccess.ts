/**
 * Signaal wanneer een API-request slaagt.
 * Gebruikt door useNetworkStatus: als we "Offline" staan maar een request
 * (bijv. getTechniques) slaagt, zetten we ons weer op "online".
 */
const listeners = new Set<() => void>();

export const apiSuccess = {
  on(fn: () => void): () => void {
    listeners.add(fn);
    return () => {
      listeners.delete(fn);
    };
  },
  emit(): void {
    listeners.forEach((fn) => {
      try {
        fn();
      } catch (e) {
        // ignore
      }
    });
  },
};
