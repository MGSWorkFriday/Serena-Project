/**
 * Theme configuration
 * Colors, typography, spacing, and other design tokens
 */

import { Platform, Dimensions } from 'react-native';
import { lightColors, darkColors, type ColorScheme } from './colors';

const tintColorLight = '#3b82f6';
const tintColorDark = '#60a5fa';

export const Colors = {
  light: {
    ...lightColors,
    tint: tintColorLight,
    icon: lightColors.textSecondary,
    tabIconDefault: lightColors.textTertiary,
    tabIconSelected: tintColorLight,
  },
  dark: {
    ...darkColors,
    tint: tintColorDark,
    icon: darkColors.textSecondary,
    tabIconDefault: darkColors.textTertiary,
    tabIconSelected: tintColorDark,
  },
};

// Spacing system
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

// Border radius
export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
} as const;

// Screen dimensions
const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Breakpoints
export const breakpoints = {
  phone: 0,
  tablet: 768,
  desktop: 1024,
} as const;

// Responsive utilities
export const isTablet = screenWidth >= breakpoints.tablet;
export const isPhone = screenWidth < breakpoints.tablet;

// Responsive values
export const responsive = {
  padding: isTablet ? spacing.lg : spacing.md,
  cardPadding: isTablet ? spacing.xl : spacing.md,
  fontSize: {
    xs: isTablet ? 12 : 10,
    sm: isTablet ? 14 : 12,
    md: isTablet ? 16 : 14,
    lg: isTablet ? 18 : 16,
    xl: isTablet ? 24 : 20,
    xxl: isTablet ? 32 : 28,
  },
} as const;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    serif: "Georgia, 'Times New Roman', serif",
    rounded: "'SF Pro Rounded', 'Hiragino Maru Gothic ProN', Meiryo, 'MS PGothic', sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  },
});
