/**
 * Settings List Component
 * Reusable component for settings sections
 */
import { View, StyleSheet, TouchableOpacity, Switch, TextInput, Alert } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';

export interface SettingItem {
  id: string;
  title: string;
  subtitle?: string;
  type: 'toggle' | 'text' | 'button' | 'info';
  value?: boolean | string;
  onPress?: () => void;
  onValueChange?: (value: boolean | string) => void;
  icon?: string;
  disabled?: boolean;
  destructive?: boolean;
}

interface SettingsListProps {
  title?: string;
  items: SettingItem[];
}

export function SettingsList({ title, items }: SettingsListProps) {
  const renderItem = (item: SettingItem) => {
    switch (item.type) {
      case 'toggle':
        return (
          <View key={item.id} style={styles.item}>
            <View style={styles.itemContent}>
              {item.icon && (
                <IconSymbol
                  name={item.icon as any}
                  size={20}
                  color={item.disabled ? '#6b7280' : '#3b82f6'}
                />
              )}
              <View style={styles.itemText}>
                <ThemedText type="defaultSemiBold" style={item.disabled && styles.disabledText}>
                  {item.title}
                </ThemedText>
                {item.subtitle && (
                  <ThemedText style={[styles.subtitle, item.disabled && styles.disabledText]}>
                    {item.subtitle}
                  </ThemedText>
                )}
              </View>
            </View>
            <Switch
              value={item.value as boolean}
              onValueChange={(value) => item.onValueChange?.(value)}
              disabled={item.disabled}
              trackColor={{ false: '#6b7280', true: '#3b82f6' }}
              thumbColor="#fff"
            />
          </View>
        );

      case 'text':
        return (
          <View key={item.id} style={styles.item}>
            <View style={styles.itemContent}>
              {item.icon && (
                <IconSymbol
                  name={item.icon as any}
                  size={20}
                  color={item.disabled ? '#6b7280' : '#3b82f6'}
                />
              )}
              <View style={styles.itemText}>
                <ThemedText type="defaultSemiBold" style={item.disabled && styles.disabledText}>
                  {item.title}
                </ThemedText>
                {item.subtitle && (
                  <ThemedText style={[styles.subtitle, item.disabled && styles.disabledText]}>
                    {item.subtitle}
                  </ThemedText>
                )}
              </View>
            </View>
            <TextInput
              style={styles.textInput}
              value={item.value as string}
              onChangeText={(text) => item.onValueChange?.(text)}
              placeholder="Enter value..."
              placeholderTextColor="#6b7280"
              editable={!item.disabled}
            />
          </View>
        );

      case 'button':
        return (
          <TouchableOpacity
            key={item.id}
            style={[
              styles.item,
              styles.buttonItem,
              item.disabled && styles.disabledItem,
              item.destructive && styles.destructiveItem,
            ]}
            onPress={item.onPress}
            disabled={item.disabled}>
            <View style={styles.itemContent}>
              {item.icon && (
                <IconSymbol
                  name={item.icon as any}
                  size={20}
                  color={item.destructive ? '#ef4444' : item.disabled ? '#6b7280' : '#3b82f6'}
                />
              )}
              <View style={styles.itemText}>
                <ThemedText
                  type="defaultSemiBold"
                  style={[
                    item.destructive && styles.destructiveText,
                    item.disabled && styles.disabledText,
                  ]}>
                  {item.title}
                </ThemedText>
                {item.subtitle && (
                  <ThemedText
                    style={[
                      styles.subtitle,
                      item.disabled && styles.disabledText,
                      item.destructive && styles.destructiveText,
                    ]}>
                    {item.subtitle}
                  </ThemedText>
                )}
              </View>
            </View>
            <IconSymbol
              name="chevron.right"
              size={16}
              color={item.disabled ? '#6b7280' : '#9ca3af'}
            />
          </TouchableOpacity>
        );

      case 'info':
        return (
          <View key={item.id} style={styles.item}>
            <View style={styles.itemContent}>
              {item.icon && (
                <IconSymbol
                  name={item.icon as any}
                  size={20}
                  color="#6b7280"
                />
              )}
              <View style={styles.itemText}>
                <ThemedText type="defaultSemiBold">{item.title}</ThemedText>
                {item.subtitle && <ThemedText style={styles.subtitle}>{item.subtitle}</ThemedText>}
                {item.value && (
                  <ThemedText style={styles.valueText}>{item.value as string}</ThemedText>
                )}
              </View>
            </View>
          </View>
        );

      default:
        return null;
    }
  };

  return (
    <ThemedView style={styles.container}>
      {title && (
        <ThemedText type="subtitle" style={styles.sectionTitle}>
          {title}
        </ThemedText>
      )}
      <ThemedView style={styles.list}>
        {items.map((item) => renderItem(item))}
      </ThemedView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  list: {
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(128, 128, 128, 0.1)',
  },
  buttonItem: {
    // Additional styles for button items
  },
  disabledItem: {
    opacity: 0.5,
  },
  destructiveItem: {
    // Styles for destructive actions
  },
  itemContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  itemText: {
    flex: 1,
  },
  subtitle: {
    fontSize: 13,
    opacity: 0.7,
    marginTop: 2,
  },
  valueText: {
    fontSize: 12,
    opacity: 0.6,
    marginTop: 4,
    fontFamily: 'monospace',
  },
  disabledText: {
    opacity: 0.5,
  },
  destructiveText: {
    color: '#ef4444',
  },
  textInput: {
    minWidth: 150,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    color: '#fff',
    fontSize: 14,
    borderWidth: 1,
    borderColor: 'rgba(128, 128, 128, 0.2)',
  },
});
