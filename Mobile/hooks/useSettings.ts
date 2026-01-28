/**
 * React hook for settings management
 */
import { useState, useEffect, useCallback } from 'react';
import { storageService } from '@/services/storage';
import { audioService } from '@/services/audio/audioService';
import { config } from '@/constants/config';

export interface AppSettings {
  audioEnabled: boolean;
  apiBaseUrl: string | null;
  paramVersion: string | null;
  feedbackRulesEnabled: boolean;
}

export function useSettings() {
  const [settings, setSettings] = useState<AppSettings>({
    audioEnabled: true,
    apiBaseUrl: null,
    paramVersion: null,
    feedbackRulesEnabled: true,
  });
  const [loading, setLoading] = useState(true);

  // Load settings from storage
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [audioEnabled, apiBaseUrl, paramVersion, feedbackRulesEnabled] = await Promise.all([
        storageService.getAudioEnabled(),
        storageService.getApiBaseUrl(),
        storageService.getParamVersion(),
        storageService.getFeedbackRulesEnabled(),
      ]);

      setSettings({
        audioEnabled,
        apiBaseUrl,
        paramVersion,
        feedbackRulesEnabled,
      });

      // Apply audio setting
      audioService.setEnabled(audioEnabled);
    } catch (error) {
      console.error('[Settings] Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateAudioEnabled = useCallback(async (enabled: boolean) => {
    try {
      await storageService.setAudioEnabled(enabled);
      audioService.setEnabled(enabled);
      setSettings((prev) => ({ ...prev, audioEnabled: enabled }));
    } catch (error) {
      console.error('[Settings] Failed to update audio setting:', error);
      throw error;
    }
  }, []);

  const updateApiBaseUrl = useCallback(async (url: string) => {
    try {
      await storageService.setApiBaseUrl(url);
      setSettings((prev) => ({ ...prev, apiBaseUrl: url }));
      // Note: API client would need to be reinitialized to use new URL
      // This is a development-only feature
    } catch (error) {
      console.error('[Settings] Failed to update API URL:', error);
      throw error;
    }
  }, []);

  const updateParamVersion = useCallback(async (version: string) => {
    try {
      await storageService.setParamVersion(version);
      setSettings((prev) => ({ ...prev, paramVersion: version }));
    } catch (error) {
      console.error('[Settings] Failed to update param version:', error);
      throw error;
    }
  }, []);

  const updateFeedbackRulesEnabled = useCallback(async (enabled: boolean) => {
    try {
      await storageService.setFeedbackRulesEnabled(enabled);
      setSettings((prev) => ({ ...prev, feedbackRulesEnabled: enabled }));
    } catch (error) {
      console.error('[Settings] Failed to update feedback rules setting:', error);
      throw error;
    }
  }, []);

  const resetApiBaseUrl = useCallback(async () => {
    try {
      await storageService.remove('@serena:api_base_url');
      setSettings((prev) => ({ ...prev, apiBaseUrl: null }));
    } catch (error) {
      console.error('[Settings] Failed to reset API URL:', error);
      throw error;
    }
  }, []);

  const clearAllData = useCallback(async () => {
    try {
      await storageService.clear();
      // Reload settings with defaults
      await loadSettings();
    } catch (error) {
      console.error('[Settings] Failed to clear data:', error);
      throw error;
    }
  }, []);

  return {
    settings,
    loading,
    updateAudioEnabled,
    updateApiBaseUrl,
    updateParamVersion,
    updateFeedbackRulesEnabled,
    resetApiBaseUrl,
    clearAllData,
    reload: loadSettings,
  };
}
