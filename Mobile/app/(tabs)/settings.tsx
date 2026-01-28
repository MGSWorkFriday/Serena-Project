/**
 * Settings Screen
 * App configuration and preferences
 */
import { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
  TextInput,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { SettingsList, type SettingItem } from '@/components/settings/SettingsList';
import { useSettings } from '@/hooks/useSettings';
import { useParameterSets } from '@/hooks/useParameterSets';
import { useFeedbackRules } from '@/hooks/useFeedbackRules';
import { config } from '@/constants/config';
import Constants from 'expo-constants';

export default function SettingsScreen() {
  const {
    settings,
    loading,
    updateAudioEnabled,
    updateApiBaseUrl,
    updateParamVersion,
    updateFeedbackRulesEnabled,
    resetApiBaseUrl,
    clearAllData,
  } = useSettings();

  const { data: parameterSets, isLoading: loadingParamSets } = useParameterSets();
  const { data: feedbackRules, isLoading: loadingFeedbackRules } = useFeedbackRules();

  const [apiUrlModalVisible, setApiUrlModalVisible] = useState(false);
  const [apiUrlInput, setApiUrlInput] = useState('');

  const handleApiUrlPress = () => {
    setApiUrlInput(settings.apiBaseUrl || config.api.baseUrl);
    setApiUrlModalVisible(true);
  };

  const handleApiUrlSave = async () => {
    try {
      if (apiUrlInput.trim()) {
        await updateApiBaseUrl(apiUrlInput.trim());
        Alert.alert('Succes', 'API URL is bijgewerkt. Herstart de app om de wijziging toe te passen.');
      } else {
        await resetApiBaseUrl();
        Alert.alert('Succes', 'API URL is gereset naar de standaard waarde.');
      }
      setApiUrlModalVisible(false);
    } catch (error) {
      Alert.alert('Fout', 'Kon API URL niet bijwerken');
    }
  };

  const handleParamVersionSelect = (version: string) => {
    Alert.alert(
      'Parameter Versie',
      `Weet je zeker dat je parameter versie "${version}" wilt selecteren?`,
      [
        { text: 'Annuleren', style: 'cancel' },
        {
          text: 'Selecteren',
          onPress: async () => {
            try {
              await updateParamVersion(version);
              Alert.alert('Succes', 'Parameter versie is bijgewerkt');
            } catch (error) {
              Alert.alert('Fout', 'Kon parameter versie niet bijwerken');
            }
          },
        },
      ]
    );
  };

  const handleClearData = () => {
    Alert.alert(
      'Alle Data Wissen',
      'Weet je zeker dat je alle opgeslagen data wilt wissen? Dit kan niet ongedaan worden gemaakt.',
      [
        { text: 'Annuleren', style: 'cancel' },
        {
          text: 'Wissen',
          style: 'destructive',
          onPress: async () => {
            try {
              await clearAllData();
              Alert.alert('Succes', 'Alle data is gewist');
            } catch (error) {
              Alert.alert('Fout', 'Kon data niet wissen');
            }
          },
        },
      ]
    );
  };

  // General settings
  const generalSettings: SettingItem[] = [
    {
      id: 'audio',
      title: 'Audio Feedback',
      subtitle: 'Schakel audio feedback in of uit',
      type: 'toggle',
      value: settings.audioEnabled,
      onValueChange: (value) => updateAudioEnabled(value as boolean),
      icon: 'speaker.wave.2.fill',
    },
    {
      id: 'feedback_rules',
      title: 'Feedback Regels',
      subtitle: 'Gebruik feedback regels van de server',
      type: 'toggle',
      value: settings.feedbackRulesEnabled,
      onValueChange: (value) => updateFeedbackRulesEnabled(value as boolean),
      icon: 'info.circle.fill',
      disabled: loadingFeedbackRules,
    },
  ];

  // Development settings
  const developmentSettings: SettingItem[] = [
    {
      id: 'api_url',
      title: 'API URL',
      subtitle: settings.apiBaseUrl || config.api.baseUrl,
      type: 'button',
      onPress: handleApiUrlPress,
      icon: 'server.rack',
    },
    {
      id: 'param_version',
      title: 'Parameter Versie',
      subtitle: settings.paramVersion || 'Standaard',
      type: 'button',
      onPress: () => {
        // Show parameter version selector
        if (parameterSets && parameterSets.length > 0) {
          Alert.alert(
            'Parameter Versie',
            'Selecteer een parameter versie:',
            [
              ...parameterSets.map((ps) => ({
                text: `${ps.version}${ps.is_default ? ' (standaard)' : ''}`,
                onPress: () => handleParamVersionSelect(ps.version),
              })),
              { text: 'Annuleren', style: 'cancel' },
            ]
          );
        } else {
          Alert.alert('Geen parameter versies', 'Er zijn geen parameter versies beschikbaar');
        }
      },
      icon: 'slider.horizontal.3',
      disabled: loadingParamSets || !parameterSets || parameterSets.length === 0,
    },
  ];

  // About settings
  const aboutSettings: SettingItem[] = [
    {
      id: 'version',
      title: 'App Versie',
      subtitle: Constants.expoConfig?.version || '1.0.0',
      type: 'info',
      icon: 'info.circle.fill',
    },
    {
      id: 'build',
      title: 'Build',
      subtitle: String(Constants.expoConfig?.ios?.buildNumber || Constants.expoConfig?.android?.versionCode || 'N/A'),
      type: 'info',
      icon: 'number',
    },
    {
      id: 'api_version',
      title: 'API Versie',
      subtitle: config.api.v1Prefix,
      type: 'info',
      icon: 'server.rack',
    },
  ];

  // Danger zone
  const dangerSettings: SettingItem[] = [
    {
      id: 'clear_data',
      title: 'Alle Data Wissen',
      subtitle: 'Wis alle opgeslagen instellingen en data',
      type: 'button',
      onPress: handleClearData,
      icon: 'trash.fill',
      destructive: true,
    },
  ];

  if (loading) {
    return (
      <ThemedView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <ThemedText style={styles.loadingText}>Instellingen laden...</ThemedText>
        </View>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <ThemedText type="title" style={styles.title}>
            Instellingen
          </ThemedText>
        </View>

        {/* General Settings */}
        <SettingsList title="Algemeen" items={generalSettings} />

        {/* Development Settings */}
        {__DEV__ && <SettingsList title="Ontwikkeling" items={developmentSettings} />}

        {/* About */}
        <SettingsList title="Over" items={aboutSettings} />

        {/* Danger Zone */}
        <SettingsList title="Gevaarlijke Zone" items={dangerSettings} />
      </ScrollView>

      {/* API URL Modal */}
      <Modal
        visible={apiUrlModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setApiUrlModalVisible(false)}>
        <ThemedView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => setApiUrlModalVisible(false)}
              style={styles.modalCloseButton}>
              <IconSymbol name="xmark" size={24} color="#fff" />
            </TouchableOpacity>
            <ThemedText type="title" style={styles.modalTitle}>
              API URL Configureren
            </ThemedText>
            <View style={styles.placeholder} />
          </View>

          <View style={styles.modalContent}>
            <ThemedText style={styles.modalLabel}>
              Voer de API base URL in (bijv. http://localhost:8000)
            </ThemedText>
            <TextInput
              style={styles.modalInput}
              value={apiUrlInput}
              onChangeText={setApiUrlInput}
              placeholder="http://localhost:8000"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
            <ThemedText style={styles.modalHint}>
              Laat leeg om de standaard waarde te gebruiken
            </ThemedText>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                onPress={() => setApiUrlModalVisible(false)}
                style={[styles.modalButton, styles.modalButtonCancel]}>
                <ThemedText style={styles.modalButtonText}>Annuleren</ThemedText>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={handleApiUrlSave}
                style={[styles.modalButton, styles.modalButtonSave]}>
                <ThemedText style={[styles.modalButtonText, styles.modalButtonTextSave]}>
                  Opslaan
                </ThemedText>
              </TouchableOpacity>
            </View>
          </View>
        </ThemedView>
      </Modal>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingBottom: 12,
  },
  title: {
    fontSize: 28,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    opacity: 0.7,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    paddingBottom: 12,
  },
  modalCloseButton: {
    padding: 8,
  },
  modalTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 20,
  },
  placeholder: {
    width: 40,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalLabel: {
    fontSize: 16,
    marginBottom: 12,
    opacity: 0.8,
  },
  modalInput: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.2)',
    marginBottom: 8,
  },
  modalHint: {
    fontSize: 12,
    opacity: 0.6,
    marginBottom: 24,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  modalButtonCancel: {
    backgroundColor: 'rgba(128, 128, 128, 0.2)',
  },
  modalButtonSave: {
    backgroundColor: '#3b82f6',
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalButtonTextSave: {
    color: '#fff',
  },
});
