/**
 * Audio Feedback Service
 * Handles Text-to-Speech for guidance feedback
 */
import * as Speech from 'expo-speech';

class AudioService {
  private enabled: boolean = true;
  private currentUtterance: string | null = null;

  /**
   * Enable or disable audio feedback
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (!enabled) {
      this.stop();
    }
  }

  /**
   * Check if audio is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Speak text using TTS
   */
  async speak(text: string, options?: { language?: string; pitch?: number; rate?: number }): Promise<void> {
    if (!this.enabled || !text) {
      return;
    }

    // Stop any current speech
    this.stop();

    try {
      await Speech.speak(text, {
        language: options?.language || 'nl-NL',
        pitch: options?.pitch || 1.0,
        rate: options?.rate || 0.9,
        onDone: () => {
          this.currentUtterance = null;
        },
        onStopped: () => {
          this.currentUtterance = null;
        },
        onError: (error) => {
          console.error('[Audio] TTS error:', error);
          this.currentUtterance = null;
        },
      });
      this.currentUtterance = text;
    } catch (error) {
      console.error('[Audio] Failed to speak:', error);
    }
  }

  /**
   * Stop current speech
   */
  stop(): void {
    if (this.currentUtterance) {
      Speech.stop();
      this.currentUtterance = null;
    }
  }

  /**
   * Check if currently speaking
   */
  async isSpeaking(): Promise<boolean> {
    try {
      return await Speech.isSpeakingAsync();
    } catch {
      return false;
    }
  }

  /**
   * Get available voices
   */
  async getAvailableVoices(): Promise<Speech.Voice[]> {
    try {
      return await Speech.getAvailableVoicesAsync();
    } catch {
      return [];
    }
  }
}

// Export singleton instance
export const audioService = new AudioService();
export default audioService;
