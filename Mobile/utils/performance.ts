/**
 * Performance Monitoring Utilities
 * Tools for tracking app performance metrics
 */

interface PerformanceMetric {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map();
  private enabled: boolean = __DEV__;

  /**
   * Start tracking a performance metric
   */
  start(name: string, metadata?: Record<string, any>): void {
    if (!this.enabled) return;

    this.metrics.set(name, {
      name,
      startTime: performance.now(),
      metadata,
    });
  }

  /**
   * End tracking a performance metric
   */
  end(name: string): number | null {
    if (!this.enabled) return null;

    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`[Performance] Metric "${name}" not found`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - metric.startTime;

    metric.endTime = endTime;
    metric.duration = duration;

    if (__DEV__) {
      console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms`, metric.metadata);
    }

    return duration;
  }

  /**
   * Get all metrics
   */
  getMetrics(): PerformanceMetric[] {
    return Array.from(this.metrics.values());
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics.clear();
  }

  /**
   * Get summary statistics
   */
  getSummary(): {
    total: number;
    average: number;
    min: number;
    max: number;
  } {
    const durations = this.getMetrics()
      .map((m) => m.duration)
      .filter((d): d is number => d !== undefined);

    if (durations.length === 0) {
      return { total: 0, average: 0, min: 0, max: 0 };
    }

    const total = durations.reduce((sum, d) => sum + d, 0);
    const average = total / durations.length;
    const min = Math.min(...durations);
    const max = Math.max(...durations);

    return { total, average, min, max };
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * Measure function execution time
 */
export function measurePerformance<T>(
  name: string,
  fn: () => T,
  metadata?: Record<string, any>
): T {
  performanceMonitor.start(name, metadata);
  try {
    const result = fn();
    if (result instanceof Promise) {
      return result.finally(() => performanceMonitor.end(name)) as T;
    }
    performanceMonitor.end(name);
    return result;
  } catch (error) {
    performanceMonitor.end(name);
    throw error;
  }
}

/**
 * Measure async function execution time
 */
export async function measurePerformanceAsync<T>(
  name: string,
  fn: () => Promise<T>,
  metadata?: Record<string, any>
): Promise<T> {
  performanceMonitor.start(name, metadata);
  try {
    const result = await fn();
    performanceMonitor.end(name);
    return result;
  } catch (error) {
    performanceMonitor.end(name);
    throw error;
  }
}

/**
 * Memory usage monitoring
 */
export function getMemoryUsage(): {
  used: number;
  total: number;
  percentage: number;
} {
  if (typeof performance.memory === 'undefined') {
    return { used: 0, total: 0, percentage: 0 };
  }

  const used = performance.memory.usedJSHeapSize;
  const total = performance.memory.totalJSHeapSize;
  const percentage = (used / total) * 100;

  return { used, total, percentage };
}

/**
 * Log memory usage
 */
export function logMemoryUsage(label?: string): void {
  if (!__DEV__) return;

  const usage = getMemoryUsage();
  console.log(
    `[Memory] ${label || 'Current'}: ${(usage.used / 1024 / 1024).toFixed(2)}MB / ${(
      usage.total /
      1024 /
      1024
    ).toFixed(2)}MB (${usage.percentage.toFixed(1)}%)`
  );
}
