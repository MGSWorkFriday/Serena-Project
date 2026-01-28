/**
 * Color System
 * Comprehensive color palette for the app
 */

export const colors = {
  // Primary colors
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6', // Main primary
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },

  // Success/Green
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },

  // Warning/Orange
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },

  // Error/Red
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },

  // Neutral/Gray
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },

  // Semantic colors
  semantic: {
    info: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    accent: '#8b5cf6',
  },
} as const;

// Light theme colors
export const lightColors = {
  background: '#ffffff',
  surface: '#f9fafb',
  surfaceVariant: '#f3f4f6',
  text: '#111827',
  textSecondary: '#6b7280',
  textTertiary: '#9ca3af',
  border: '#e5e7eb',
  borderLight: '#f3f4f6',
  divider: '#e5e7eb',
  primary: colors.primary[500],
  primaryDark: colors.primary[600],
  primaryLight: colors.primary[400],
  success: colors.success[600],
  warning: colors.warning[500],
  error: colors.error[500],
  info: colors.primary[500],
  accent: colors.semantic.accent,
  card: '#ffffff',
  cardBorder: '#e5e7eb',
  shadow: 'rgba(0, 0, 0, 0.1)',
  overlay: 'rgba(0, 0, 0, 0.5)',
} as const;

// Dark theme colors
export const darkColors = {
  background: '#111827',
  surface: '#1f2937',
  surfaceVariant: '#374151',
  text: '#f9fafb',
  textSecondary: '#d1d5db',
  textTertiary: '#9ca3af',
  border: '#374151',
  borderLight: '#4b5563',
  divider: '#374151',
  primary: colors.primary[400],
  primaryDark: colors.primary[500],
  primaryLight: colors.primary[300],
  success: colors.success[500],
  warning: colors.warning[400],
  error: colors.error[400],
  info: colors.primary[400],
  accent: colors.semantic.accent,
  card: '#1f2937',
  cardBorder: '#374151',
  shadow: 'rgba(0, 0, 0, 0.3)',
  overlay: 'rgba(0, 0, 0, 0.7)',
} as const;

export type ColorScheme = 'light' | 'dark';

export function getColors(scheme: ColorScheme) {
  return scheme === 'dark' ? darkColors : lightColors;
}
