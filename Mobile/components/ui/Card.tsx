/**
 * Card Component
 * Reusable card component with theming
 */
import { View, StyleSheet, ViewStyle } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Colors, spacing, borderRadius } from '@/constants/theme';
import { isTablet } from '@/utils/responsive';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: keyof typeof spacing;
}

export function Card({ children, style, variant = 'default', padding = 'md' }: CardProps) {
  const colorScheme = useColorScheme() ?? 'light';
  const themeColors = Colors[colorScheme];

  const cardStyle: ViewStyle = {
    backgroundColor: themeColors.card,
    padding: spacing[padding],
    borderRadius: borderRadius.lg,
  };

  if (variant === 'outlined') {
    cardStyle.borderWidth = 1;
    cardStyle.borderColor = themeColors.cardBorder;
  } else if (variant === 'elevated') {
    cardStyle.shadowColor = themeColors.shadow;
    cardStyle.shadowOffset = { width: 0, height: 2 };
    cardStyle.shadowOpacity = 0.1;
    cardStyle.shadowRadius = 4;
    cardStyle.elevation = 3;
  }

  return (
    <ThemedView style={[cardStyle, style]} variant="card">
      {children}
    </ThemedView>
  );
}
