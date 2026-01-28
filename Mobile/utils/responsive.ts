/**
 * Responsive Design Utilities
 * Helper functions for responsive layouts
 */
import { Dimensions, Platform } from 'react-native';
import { breakpoints } from '@/constants/theme';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export const isTablet = screenWidth >= breakpoints.tablet;
export const isPhone = screenWidth < breakpoints.tablet;
export const isSmallPhone = screenWidth < 375;
export const isLargePhone = screenWidth >= 375 && screenWidth < breakpoints.tablet;

/**
 * Get responsive value based on screen size
 */
export function useResponsiveValue<T>(phoneValue: T, tabletValue: T): T {
  return isTablet ? tabletValue : phoneValue;
}

/**
 * Get responsive padding
 */
export function getResponsivePadding() {
  return isTablet ? 24 : 16;
}

/**
 * Get responsive font size
 */
export function getResponsiveFontSize(baseSize: number): number {
  return isTablet ? baseSize * 1.2 : baseSize;
}

/**
 * Get number of columns for grid layouts
 */
export function getGridColumns(): number {
  if (isTablet) {
    return screenWidth >= 1024 ? 3 : 2;
  }
  return 1;
}

/**
 * Get card width for list items
 */
export function getCardWidth(): number {
  if (isTablet) {
    return (screenWidth - 48) / 2; // 2 columns with padding
  }
  return screenWidth - 32; // Full width with padding
}

export { screenWidth, screenHeight };
