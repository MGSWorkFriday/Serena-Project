/**
 * Unit Tests for Storage Service
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { storageService } from '@/services/storage';

describe('Storage Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('get', () => {
    it('should return stored value', async () => {
      const testData = { key: 'value' };
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(JSON.stringify(testData));

      const result = await storageService.get('test-key', null);
      expect(result).toEqual(testData);
      expect(AsyncStorage.getItem).toHaveBeenCalledWith('test-key');
    });

    it('should return default value when key does not exist', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const result = await storageService.get('non-existent', 'default');
      expect(result).toBe('default');
    });

    it('should handle JSON parse errors', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('invalid json');
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      const result = await storageService.get('invalid-key', 'default');
      expect(result).toBe('default');
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('set', () => {
    it('should store value', async () => {
      const testData = { key: 'value' };
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);

      await storageService.set('test-key', testData);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('test-key', JSON.stringify(testData));
    });

    it('should handle storage errors', async () => {
      const error = new Error('Storage error');
      (AsyncStorage.setItem as jest.Mock).mockRejectedValue(error);
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      await expect(storageService.set('test-key', 'value')).rejects.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('remove', () => {
    it('should remove key', async () => {
      (AsyncStorage.removeItem as jest.Mock).mockResolvedValue(undefined);

      await storageService.remove('test-key');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('test-key');
    });
  });

  describe('clear', () => {
    it('should clear all storage', async () => {
      (AsyncStorage.clear as jest.Mock).mockResolvedValue(undefined);

      await storageService.clear();
      expect(AsyncStorage.clear).toHaveBeenCalled();
    });
  });

  describe('getAllKeys', () => {
    it('should return all keys', async () => {
      const keys = ['key1', 'key2', 'key3'];
      (AsyncStorage.getAllKeys as jest.Mock).mockResolvedValue(keys);

      const result = await storageService.getAllKeys();
      expect(result).toEqual(keys);
    });
  });
});
