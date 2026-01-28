import { StyleSheet, Text, type TextProps } from 'react-native';

import { useThemeColor } from '@/hooks/use-theme-color';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Colors } from '@/constants/theme';
import { getResponsiveFontSize } from '@/utils/responsive';

export type ThemedTextProps = TextProps & {
  lightColor?: string;
  darkColor?: string;
  type?: 'default' | 'title' | 'defaultSemiBold' | 'subtitle' | 'link' | 'caption';
  variant?: 'primary' | 'secondary' | 'tertiary' | 'error' | 'success' | 'warning';
};

export function ThemedText({
  style,
  lightColor,
  darkColor,
  type = 'default',
  variant,
  ...rest
}: ThemedTextProps) {
  const colorScheme = useColorScheme() ?? 'light';
  const themeColors = Colors[colorScheme];

  // Determine text color
  let textColor = useThemeColor({ light: lightColor, dark: darkColor }, 'text');
  if (variant) {
    switch (variant) {
      case 'primary':
        textColor = themeColors.primary;
        break;
      case 'secondary':
        textColor = themeColors.textSecondary;
        break;
      case 'tertiary':
        textColor = themeColors.textTertiary;
        break;
      case 'error':
        textColor = themeColors.error;
        break;
      case 'success':
        textColor = themeColors.success;
        break;
      case 'warning':
        textColor = themeColors.warning;
        break;
    }
  }

  return (
    <Text
      style={[
        { color: textColor },
        type === 'default' ? styles.default : undefined,
        type === 'title' ? styles.title : undefined,
        type === 'defaultSemiBold' ? styles.defaultSemiBold : undefined,
        type === 'subtitle' ? styles.subtitle : undefined,
        type === 'link' ? styles.link : undefined,
        type === 'caption' ? styles.caption : undefined,
        style,
      ]}
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  default: {
    fontSize: getResponsiveFontSize(16),
    lineHeight: getResponsiveFontSize(24),
  },
  defaultSemiBold: {
    fontSize: getResponsiveFontSize(16),
    lineHeight: getResponsiveFontSize(24),
    fontWeight: '600',
  },
  title: {
    fontSize: getResponsiveFontSize(32),
    fontWeight: 'bold',
    lineHeight: getResponsiveFontSize(40),
  },
  subtitle: {
    fontSize: getResponsiveFontSize(20),
    fontWeight: '600',
    lineHeight: getResponsiveFontSize(28),
  },
  link: {
    lineHeight: getResponsiveFontSize(24),
    fontSize: getResponsiveFontSize(16),
    textDecorationLine: 'underline',
  },
  caption: {
    fontSize: getResponsiveFontSize(12),
    lineHeight: getResponsiveFontSize(16),
    opacity: 0.7,
  },
});
