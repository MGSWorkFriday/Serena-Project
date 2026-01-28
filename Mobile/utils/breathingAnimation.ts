/**
 * Breathing animation calculations
 * Migrated from breathing_logic.py
 */

/**
 * Calculate Y value (-1 to 1) for breathing cycle
 * @param tInCycle Time within the cycle (seconds)
 * @param a Inhale time (seconds)
 * @param b Hold1 time after inhale (seconds)
 * @param c Exhale time (seconds)
 * @param d Hold2 time after exhale (seconds)
 * @returns Y value between -1 (bottom/exhale) and 1 (top/inhale)
 */
export function calculateBreathY(
  tInCycle: number,
  a: number,
  b: number,
  c: number,
  d: number
): number {
  if (a + b + c + d <= 0) {
    return 0.0;
  }

  // Phase 1: Inhale (sine curve going up)
  if (tInCycle < a && a > 0) {
    return Math.sin(-Math.PI / 2 + Math.PI * (tInCycle / Math.max(1e-6, a)));
  }

  let t = tInCycle - a;

  // Phase 2: Hold 1 (hold at top)
  if (t < b && b > 0) {
    return 1.0;
  }

  t -= b;

  // Phase 3: Exhale (sine curve going down)
  if (t < c && c > 0) {
    return Math.sin(Math.PI / 2 + Math.PI * (t / Math.max(1e-6, c)));
  }

  // Phase 4: Hold 2 (hold at bottom)
  return -1.0;
}

/**
 * Calculate total cycle duration
 */
export function getCycleDuration(
  a: number,
  b: number,
  c: number,
  d: number
): number {
  return a + b + c + d;
}

/**
 * Generate preview data for breathing cycle
 * Used for drawing the preview curve
 */
export function generatePreviewData(
  a: number,
  b: number,
  c: number,
  d: number,
  sampleRate: number = 30 // samples per second
): { x: number[]; y: number[] } {
  const duration = getCycleDuration(a, b, c, d);
  const samples = Math.ceil(duration * sampleRate);
  const x: number[] = [];
  const y: number[] = [];

  for (let i = 0; i < samples; i++) {
    const t = (i / samples) * duration;
    x.push(t);
    y.push(calculateBreathY(t, a, b, c, d));
  }

  return { x, y };
}
