/**
 * Unit Tests for Responsive Utilities
 */
import { Dimensions } from 'react-native';
import {
  isTablet,
  isPhone,
  getResponsivePadding,
  getResponsiveFontSize,
  getGridColumns,
  getCardWidth,
  useResponsiveValue,
} from '@/utils/responsive';

// Mock Dimensions
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Dimensions: {
      get: jest.fn(),
    },
  };
});

describe('Responsive Utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('isTablet', () => {
    it('should return true for tablet width', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 768, height: 1024 });
      // Re-import to get fresh values
      jest.resetModules();
      const { isTablet } = require('@/utils/responsive');
      expect(isTablet).toBe(true);
    });

    it('should return false for phone width', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 375, height: 667 });
      jest.resetModules();
      const { isTablet } = require('@/utils/responsive');
      expect(isTablet).toBe(false);
    });
  });

  describe('getResponsivePadding', () => {
    it('should return 24 for tablet', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 768, height: 1024 });
      jest.resetModules();
      const { getResponsivePadding } = require('@/utils/responsive');
      expect(getResponsivePadding()).toBe(24);
    });

    it('should return 16 for phone', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 375, height: 667 });
      jest.resetModules();
      const { getResponsivePadding } = require('@/utils/responsive');
      expect(getResponsivePadding()).toBe(16);
    });
  });

  describe('getResponsiveFontSize', () => {
    it('should scale font size for tablet', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 768, height: 1024 });
      jest.resetModules();
      const { getResponsiveFontSize } = require('@/utils/responsive');
      expect(getResponsiveFontSize(16)).toBe(19.2); // 16 * 1.2
    });

    it('should return original size for phone', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 375, height: 667 });
      jest.resetModules();
      const { getResponsiveFontSize } = require('@/utils/responsive');
      expect(getResponsiveFontSize(16)).toBe(16);
    });
  });

  describe('getGridColumns', () => {
    it('should return 3 for large tablet', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 1024, height: 1366 });
      jest.resetModules();
      const { getGridColumns } = require('@/utils/responsive');
      expect(getGridColumns()).toBe(3);
    });

    it('should return 2 for tablet', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 768, height: 1024 });
      jest.resetModules();
      const { getGridColumns } = require('@/utils/responsive');
      expect(getGridColumns()).toBe(2);
    });

    it('should return 1 for phone', () => {
      (Dimensions.get as jest.Mock).mockReturnValue({ width: 375, height: 667 });
      jest.resetModules();
      const { getGridColumns } = require('@/utils/responsive');
      expect(getGridColumns()).toBe(1);
    });
  });
});
