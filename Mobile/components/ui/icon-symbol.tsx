// Fallback voor MaterialIcons op Android en web (SF Symbols op iOS).

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import type { SymbolWeight } from 'expo-symbols';
import { ComponentProps } from 'react';
import { OpaqueColorValue, type StyleProp, type TextStyle } from 'react-native';

type MaterialIconName = ComponentProps<typeof MaterialIcons>['name'];

const MAPPING: Record<string, MaterialIconName> = {
  'house.fill': 'home',
  'paperplane.fill': 'send',
  'chevron.left.forwardslash.chevron.right': 'code',
  'chevron.right': 'chevron-right',
  'lungs.fill': 'air',
  'lungs': 'air',
  'antenna.radiowaves.left.and.right': 'bluetooth',
  'heart.fill': 'favorite',
  'play.fill': 'play-arrow',
  'play.circle.fill': 'play-circle',
  'chevron.down': 'expand-more',
  'xmark.circle.fill': 'cancel',
  'xmark': 'close',
  'wifi.slash': 'wifi-off',
  'magnifyingglass': 'search',
  'clock': 'schedule',
  'clock.fill': 'schedule',
  'info.circle': 'info',
  'exclamationmark.triangle.fill': 'warning',
  'arrow.clockwise': 'refresh',
  'calendar': 'today',
  'calendar.badge.checkmark': 'check-circle',
  'target': 'gps-fixed',
  'link': 'link',
  'chevron.left': 'chevron-left',
  'stop.fill': 'stop',
  'gearshape.fill': 'settings',
  'square.and.arrow.down.fill': 'save',
};

type IconSymbolName = keyof typeof MAPPING | (string & {});

/**
 * Icon: SF Symbol naam → Material Icons op web/Android. Onbekende namen → help-outline.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
  weight?: SymbolWeight;
}) {
  const materialName = MAPPING[name] ?? 'help';
  return <MaterialIcons color={color} size={size} name={materialName} style={style} />;
}
