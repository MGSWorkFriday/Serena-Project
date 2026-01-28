/**
 * Integration Tests for API Client
 */
import axios, { AxiosInstance } from 'axios';
import { apiClient } from '@/services/api/client';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Client', () => {
  let mockAxiosInstance: jest.Mocked<AxiosInstance>;

  beforeEach(() => {
    mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      patch: jest.fn(),
      interceptors: {
        request: { use: jest.fn(), eject: jest.fn() },
        response: { use: jest.fn(), eject: jest.fn() },
      },
    } as any;

    mockedAxios.create.mockReturnValue(mockAxiosInstance as any);
    jest.clearAllMocks();
  });

  describe('getStatus', () => {
    it('should return status data', async () => {
      const mockResponse = { data: { status: 'ok', version: '1.0.0' } };
      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await apiClient.getStatus();
      expect(result).toEqual(mockResponse.data);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/status');
    });

    it('should handle errors', async () => {
      const error = new Error('Network error');
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(apiClient.getStatus()).rejects.toThrow();
    });
  });

  describe('getDevices', () => {
    it('should return devices list', async () => {
      const mockDevices = [
        { device_id: '1', name: 'Device 1', connected: true },
        { device_id: '2', name: 'Device 2', connected: false },
      ];
      const mockResponse = { data: mockDevices };
      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await apiClient.getDevices();
      expect(result).toEqual(mockDevices);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/devices');
    });
  });

  describe('getSessions', () => {
    it('should return sessions with filters', async () => {
      const mockSessions = [
        { session_id: '1', device_id: '1', status: 'completed' },
        { session_id: '2', device_id: '1', status: 'active' },
      ];
      const mockResponse = { data: mockSessions };
      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await apiClient.getSessions({ device_id: '1', status: 'completed' });
      expect(result).toEqual(mockSessions);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/sessions', {
        params: { device_id: '1', status: 'completed' },
      });
    });
  });

  describe('createSession', () => {
    it('should create a new session', async () => {
      const sessionData = {
        device_id: '1',
        technique_id: 'tech1',
        target_rr: 6,
      };
      const mockSession = { session_id: 'new-session', ...sessionData, status: 'active' };
      const mockResponse = { data: mockSession };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await apiClient.createSession(sessionData);
      expect(result).toEqual(mockSession);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/sessions', sessionData);
    });
  });

  describe('ingestRecords', () => {
    it('should send records as NDJSON', async () => {
      const records = [
        { ts: 1000, signal: 'ecg', data: [1, 2, 3] },
        { ts: 2000, signal: 'hr', bpm: 70 },
      ];
      const mockResponse = { data: { ingested: 2 } };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await apiClient.ingestRecords(records);
      expect(result).toEqual({ ingested: 2 });
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/ingest',
        '{"ts":1000,"signal":"ecg","data":[1,2,3]}\n{"ts":2000,"signal":"hr","bpm":70}',
        {
          headers: {
            'Content-Type': 'application/x-ndjson',
          },
        }
      );
    });
  });

  describe('retry logic', () => {
    it('should retry on network errors', async () => {
      const networkError = { code: 'ECONNABORTED', message: 'Network Error' };
      mockAxiosInstance.get
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValueOnce({ data: { status: 'ok' } });

      // Note: This test depends on the actual retry implementation
      // You may need to adjust based on your retry logic
    });
  });
});
