import { View, type ViewProps } from 'react-native';

import { useThemeColor } from '@/hooks/use-theme-color';

export type ThemedViewProps = ViewProps & {
  lightColor?: string;
  darkColor?: string;
  variant?: 'background' | 'surface' | 'surfaceVariant' | 'card';
};

export function ThemedView({
  style,
  lightColor,
  darkColor,
  variant = 'background',
  ...otherProps
}: ThemedViewProps) {
  const defaultColor = useThemeColor(
    { light: lightColor, dark: darkColor },
    variant === 'card' ? 'card' : variant
  );
  const backgroundColor = lightColor || darkColor || defaultColor;

  return <View style={[{ backgroundColor }, style]} {...otherProps} />;
}
