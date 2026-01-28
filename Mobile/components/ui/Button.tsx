/**
 * Button Component
 * Reusable button component with theming
 */
import { TouchableOpacity, StyleSheet, ActivityIndicator, ViewStyle, TextStyle } from 'react-native';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Colors, spacing, borderRadius } from '@/constants/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  style?: ViewStyle;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  style,
}: ButtonProps) {
  const colorScheme = useColorScheme() ?? 'light';
  const themeColors = Colors[colorScheme];

  const getButtonStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.sm,
      borderRadius: borderRadius.md,
      opacity: disabled ? 0.6 : 1,
    };

    // Size
    if (size === 'sm') {
      baseStyle.paddingHorizontal = spacing.md;
      baseStyle.paddingVertical = spacing.sm;
    } else if (size === 'lg') {
      baseStyle.paddingHorizontal = spacing.xl;
      baseStyle.paddingVertical = spacing.lg;
    } else {
      baseStyle.paddingHorizontal = spacing.lg;
      baseStyle.paddingVertical = spacing.md;
    }

    // Variant
    switch (variant) {
      case 'primary':
        baseStyle.backgroundColor = themeColors.primary;
        break;
      case 'secondary':
        baseStyle.backgroundColor = themeColors.surfaceVariant;
        break;
      case 'outline':
        baseStyle.backgroundColor = 'transparent';
        baseStyle.borderWidth = 1;
        baseStyle.borderColor = themeColors.border;
        break;
      case 'destructive':
        baseStyle.backgroundColor = themeColors.error;
        break;
    }

    if (fullWidth) {
      baseStyle.width = '100%';
    }

    return baseStyle;
  };

  const getTextStyle = (): TextStyle => {
    const textStyle: TextStyle = {
      fontWeight: '600',
    };

    if (size === 'sm') {
      textStyle.fontSize = 14;
    } else if (size === 'lg') {
      textStyle.fontSize = 18;
    } else {
      textStyle.fontSize = 16;
    }

    switch (variant) {
      case 'primary':
      case 'destructive':
        textStyle.color = '#ffffff';
        break;
      case 'secondary':
        textStyle.color = themeColors.text;
        break;
      case 'outline':
        textStyle.color = themeColors.text;
        break;
    }

    return textStyle;
  };

  const iconColor =
    variant === 'primary' || variant === 'destructive' ? '#ffffff' : themeColors.text;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={[getButtonStyle(), style]}
      activeOpacity={0.7}>
      {loading ? (
        <ActivityIndicator size="small" color={iconColor} />
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <IconSymbol name={icon as any} size={20} color={iconColor} />
          )}
          <ThemedText style={getTextStyle()}>{title}</ThemedText>
          {icon && iconPosition === 'right' && (
            <IconSymbol name={icon as any} size={20} color={iconColor} />
          )}
        </>
      )}
    </TouchableOpacity>
  );
}
