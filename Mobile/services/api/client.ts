/**
 * API Client for backend communication
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { config } from '@/constants/config';
import { apiSuccess } from './apiSuccess';
import type {
  Device,
  DeviceCreate,
  DeviceUpdate,
  Session,
  SessionCreate,
  SessionUpdate,
  SignalRecord,
  RecordIngest,
  Technique,
  TechniqueCreate,
  FeedbackRules,
  ParameterSet,
  SystemStatus,
  PaginatedResponse,
} from './types';

class ApiClient {
  private client: AxiosInstance;
  private maxRetries = 3;
  private retryDelay = 1000; // 1 second

  constructor() {
    this.client = axios.create({
      baseURL: `${config.api.baseUrl}${config.api.v1Prefix}`,
      timeout: config.api.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config: any) => {
        if (__DEV__) {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        }
        return config;
      },
      (error: any) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor: bij succes melden (voor 'Offline'→online), en error/retry
    this.client.interceptors.response.use(
      (response: any) => {
        try {
          apiSuccess.emit();
        } catch (e) {
          if (__DEV__) console.warn('[API] apiSuccess.emit error:', e);
        }
        return response;
      },
      async (error: AxiosError) => {
        const config = error.config as any;

        // Don't retry if retry count exceeded or no config
        if (!config || !this.shouldRetry(error)) {
          if (__DEV__) {
            const msg = error.response
              ? `status ${error.response?.status}`
              : `geen response (vaak CORS of netwerk); message=${String((error as Error).message)}`;
            console.error('[API] Response error:', config?.url, msg, error.response?.data);
          }
          return Promise.reject(this.handleError(error));
        }

        // Initialize retry count
        config.__retryCount = config.__retryCount || 0;

        // Check if we should retry
        if (config.__retryCount < this.maxRetries) {
          config.__retryCount += 1;

          // Wait before retrying (exponential backoff)
          const delay = this.retryDelay * Math.pow(2, config.__retryCount - 1);
          await new Promise((resolve) => setTimeout(resolve, delay));

          if (__DEV__) {
            console.log(`[API] Retrying request (${config.__retryCount}/${this.maxRetries}): ${config.url}`);
          }

          return this.client(config);
        }

        if (__DEV__) {
          console.error('[API] Response error:', error.response?.status, error.response?.data);
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private shouldRetry(error: AxiosError): boolean {
    // Retry on network errors or 5xx server errors
    if (!error.response) {
      return true; // Network error
    }
    const status = error.response.status;
    return status >= 500 && status < 600; // Server errors
  }

  private handleError(error: AxiosError): Error {
    if (error.response) {
      // Server responded with error
      const message = (error.response.data as any)?.detail || error.message;
      return new Error(message);
    } else if (error.request) {
      // Request made but no response
      return new Error('Network error: No response from server');
    } else {
      // Error setting up request
      return new Error(`Request error: ${error.message}`);
    }
  }

  // Health & Status
  /** Licht contactmoment (geen DB). Wordt gebruikt voor 'Offline'-detectie. */
  async getPing(): Promise<void> {
    await this.client.get('/ping');
  }

  async getStatus(): Promise<SystemStatus> {
    const response = await this.client.get<SystemStatus>('/status');
    return response.data;
  }

  // Devices
  async getDevices(): Promise<Device[]> {
    const response = await this.client.get<Device[]>('/devices');
    return response.data;
  }

  async getDevice(deviceId: string): Promise<Device> {
    const response = await this.client.get<Device>(`/devices/${deviceId}`);
    return response.data;
  }

  async createDevice(data: DeviceCreate): Promise<Device> {
    const response = await this.client.post<Device>('/devices', data);
    return response.data;
  }

  async updateDevice(deviceId: string, data: DeviceUpdate): Promise<Device> {
    const response = await this.client.patch<Device>(`/devices/${deviceId}`, data);
    return response.data;
  }

  async getDeviceSessions(deviceId: string): Promise<Session[]> {
    const response = await this.client.get<Session[]>(`/devices/${deviceId}/sessions`);
    return response.data;
  }

  // Sessions
  async getSessions(params?: {
    device_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    skip?: number;
  }): Promise<Session[]> {
    const response = await this.client.get<Session[]>('/sessions', { params });
    return response.data;
  }

  async getSession(sessionId: string): Promise<Session> {
    const response = await this.client.get<Session>(`/sessions/${sessionId}`);
    return response.data;
  }

  async createSession(data: SessionCreate): Promise<Session> {
    const response = await this.client.post<Session>('/sessions', data);
    return response.data;
  }

  async updateSession(sessionId: string, data: SessionUpdate): Promise<Session> {
    const response = await this.client.patch<Session>(`/sessions/${sessionId}`, data);
    return response.data;
  }

  async endSession(sessionId: string): Promise<Session> {
    const response = await this.client.post<Session>(`/sessions/${sessionId}/end`);
    return response.data;
  }

  // Signals
  async getSignals(params: {
    device_id?: string;
    session_id?: string;
    signal?: string;
    start_ts?: number;
    end_ts?: number;
    limit?: number;
    skip?: number;
  }): Promise<SignalRecord[]> {
    const response = await this.client.get<SignalRecord[]>('/signals', { params });
    return response.data;
  }

  async getRecentSignals(deviceId?: string, limit = 100): Promise<SignalRecord[]> {
    const params = deviceId ? { device_id: deviceId, limit } : { limit };
    const response = await this.client.get<SignalRecord[]>('/signals/recent', { params });
    return response.data;
  }

  async getSignal(signalId: string): Promise<SignalRecord> {
    const response = await this.client.get<SignalRecord>(`/signals/${signalId}`);
    return response.data;
  }

  // Ingest
  async ingestRecords(records: RecordIngest[]): Promise<{ ingested: number }> {
    // Try to send records
    try {
      // Send as NDJSON (newline-delimited JSON)
      const ndjson = records.map((r) => JSON.stringify(r)).join('\n');
      const response = await this.client.post<{ ingested: number }>(
        '/ingest',
        ndjson,
        {
          headers: {
            'Content-Type': 'application/x-ndjson',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      // If network error, queue for later sync
      if (!error.response || error.code === 'ECONNABORTED' || error.message?.includes('Network')) {
        try {
          const { offlineQueue } = await import('@/services/offlineQueue');
          await offlineQueue.enqueue(records);
          console.log(`[API] Queued ${records.length} records for offline sync`);
        } catch (queueError) {
          console.error('[API] Failed to queue records:', queueError);
        }
        throw new Error('Offline: Records queued for sync');
      }
      throw error;
    }
  }

  // Techniques
  async getTechniques(publicOnly = false): Promise<Technique[]> {
    const endpoint = publicOnly ? '/techniques/public' : '/techniques';
    const response = await this.client.get(endpoint);
    const data = response.data;

    // Backend returns { [name]: { name, description, param_version, show_in_app, protocol } };
    // normaliseer naar array. Soms is het direct een array.
    let arr: Technique[];
    if (Array.isArray(data)) {
      arr = data as Technique[];
    } else if (data != null && typeof data === 'object' && !Array.isArray(data)) {
      arr = Object.values(data) as Technique[];
    } else {
      if (__DEV__) {
        console.warn('[getTechniques] onverwacht response-type:', typeof data, data);
      }
      arr = [];
    }

    if (__DEV__) {
      const keys = data != null && typeof data === 'object' && !Array.isArray(data) ? Object.keys(data).length : '-';
      console.log('[getTechniques]', endpoint, 'object-keys:', keys, '→ array-length:', arr.length, arr.length ? arr[0]?.name : '');
    }
    return arr;
  }

  async getTechnique(name: string): Promise<Technique> {
    const response = await this.client.get<Technique>(`/techniques/${name}`);
    return response.data;
  }

  async createOrUpdateTechnique(data: TechniqueCreate): Promise<Technique> {
    const response = await this.client.post<Technique>('/techniques', data);
    return response.data;
  }

  async deleteTechnique(name: string): Promise<void> {
    await this.client.delete(`/techniques/${name}`);
  }

  // Feedback
  async getFeedbackRules(): Promise<FeedbackRules> {
    const response = await this.client.get<FeedbackRules>('/feedback/rules');
    return response.data;
  }

  async updateFeedbackRules(rules: Partial<FeedbackRules>): Promise<FeedbackRules> {
    const response = await this.client.post<FeedbackRules>('/feedback/rules', rules);
    return response.data;
  }

  // Parameter Sets
  async getParameterSets(): Promise<ParameterSet[]> {
    const response = await this.client.get<ParameterSet[]>('/param_versions');
    return response.data;
  }

  async getParameterSet(version: string): Promise<ParameterSet> {
    const response = await this.client.get<ParameterSet>(`/param_versions/${version}`);
    return response.data;
  }

  async createParameterSet(data: Omit<ParameterSet, '_id' | 'created_at' | 'updated_at'>): Promise<ParameterSet> {
    const response = await this.client.post<ParameterSet>('/param_versions', data);
    return response.data;
  }

  async updateParameterSet(version: string, data: Partial<ParameterSet>): Promise<ParameterSet> {
    const response = await this.client.patch<ParameterSet>(`/param_versions/${version}`, data);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
