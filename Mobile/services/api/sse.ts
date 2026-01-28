/**
 * Server-Sent Events (SSE) client for real-time signal streaming
 */
import { config } from '@/constants/config';
import type { SignalRecord, SignalType } from './types';

export interface SSEOptions {
  deviceId?: string;
  signalTypes?: SignalType[];
  onMessage: (signal: SignalRecord) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export class SSEClient {
  private eventSource: EventSource | null = null;
  private options: SSEOptions;

  constructor(options: SSEOptions) {
    this.options = options;
  }

  connect(): void {
    if (this.eventSource) {
      this.close();
    }

    // Build URL with query parameters
    const params = new URLSearchParams();
    if (this.options.deviceId) {
      params.append('device_id', this.options.deviceId);
    }
    if (this.options.signalTypes && this.options.signalTypes.length > 0) {
      this.options.signalTypes.forEach((type) => {
        params.append('signal', type);
      });
    }

    const url = `${config.api.baseUrl}${config.api.v1Prefix}/stream?${params.toString()}`;

    try {
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        if (__DEV__) {
          console.log('[SSE] Connected to stream');
        }
        this.options.onOpen?.();
      };

      this.eventSource.onmessage = (event) => {
        try {
          const signal: SignalRecord = JSON.parse(event.data);
          this.options.onMessage(signal);
        } catch (error) {
          console.error('[SSE] Error parsing message:', error);
          this.options.onError?.(new Error('Failed to parse SSE message'));
        }
      };

      this.eventSource.onerror = (error) => {
        console.error('[SSE] Connection error:', error);
        this.options.onError?.(new Error('SSE connection error'));
      };
    } catch (error) {
      console.error('[SSE] Failed to create EventSource:', error);
      this.options.onError?.(error as Error);
    }
  }

  close(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.options.onClose?.();
    }
  }

  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }
}

/**
 * React hook-friendly SSE client wrapper
 */
export function createSSEStream(options: SSEOptions): SSEClient {
  return new SSEClient(options);
}
