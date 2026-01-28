/**
 * Storage Service
 * AsyncStorage wrapper for persistent settings
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  AUDIO_ENABLED: '@serena:audio_enabled',
  API_BASE_URL: '@serena:api_base_url',
  PARAM_VERSION: '@serena:param_version',
  FEEDBACK_RULES_ENABLED: '@serena:feedback_rules_enabled',
} as const;

class StorageService {
  /**
   * Get a value from storage
   */
  async get<T>(key: string, defaultValue?: T): Promise<T | null> {
    try {
      const value = await AsyncStorage.getItem(key);
      if (value === null) {
        return defaultValue ?? null;
      }
      return JSON.parse(value) as T;
    } catch (error) {
      console.error(`[Storage] Failed to get ${key}:`, error);
      return defaultValue ?? null;
    }
  }

  /**
   * Set a value in storage
   */
  async set<T>(key: string, value: T): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`[Storage] Failed to set ${key}:`, error);
      throw error;
    }
  }

  /**
   * Remove a value from storage
   */
  async remove(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error(`[Storage] Failed to remove ${key}:`, error);
      throw error;
    }
  }

  /**
   * Clear all storage
   */
  async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('[Storage] Failed to clear:', error);
      throw error;
    }
  }

  /**
   * Get all keys
   */
  async getAllKeys(): Promise<readonly string[]> {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      console.error('[Storage] Failed to get all keys:', error);
      return [];
    }
  }

  // Audio settings
  async getAudioEnabled(): Promise<boolean> {
    const value = await this.get<boolean>(STORAGE_KEYS.AUDIO_ENABLED, true);
    return value ?? true;
  }

  async setAudioEnabled(enabled: boolean): Promise<void> {
    await this.set(STORAGE_KEYS.AUDIO_ENABLED, enabled);
  }

  // API URL settings
  async getApiBaseUrl(): Promise<string | null> {
    return await this.get<string>(STORAGE_KEYS.API_BASE_URL);
  }

  async setApiBaseUrl(url: string): Promise<void> {
    await this.set(STORAGE_KEYS.API_BASE_URL, url);
  }

  // Parameter version settings
  async getParamVersion(): Promise<string | null> {
    return await this.get<string>(STORAGE_KEYS.PARAM_VERSION);
  }

  async setParamVersion(version: string): Promise<void> {
    await this.set(STORAGE_KEYS.PARAM_VERSION, version);
  }

  // Feedback rules settings
  async getFeedbackRulesEnabled(): Promise<boolean> {
    const value = await this.get<boolean>(STORAGE_KEYS.FEEDBACK_RULES_ENABLED, true);
    return value ?? true;
  }

  async setFeedbackRulesEnabled(enabled: boolean): Promise<void> {
    await this.set(STORAGE_KEYS.FEEDBACK_RULES_ENABLED, enabled);
  }
}

// Export singleton instance
export const storageService = new StorageService();
export default storageService;
export { STORAGE_KEYS };
