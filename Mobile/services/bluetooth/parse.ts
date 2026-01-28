/**
 * Polar H10 data parsing — shared by native (base64→bytes) and web (DataView→bytes).
 * Pure functions; no React Native or DOM imports.
 */

/**
 * Parse PMD ECG bytes to samples (24-bit signed, little-endian).
 */
export function parsePmdEcgBytes(bytes: number[]): number[] {
  if (bytes.length < 3) return [];
  const samples: number[] = [];
  for (let i = 0; i <= bytes.length - 3; i += 3) {
    const byte0 = bytes[i];
    const byte1 = bytes[i + 1];
    const byte2 = bytes[i + 2];
    let sample = byte0 | (byte1 << 8) | (byte2 << 16);
    if (byte2 & 0x80) sample |= 0xff000000;
    samples.push(sample);
  }
  return samples;
}

/**
 * Parse Heart Rate characteristic bytes to { bpm, rrIntervals? }.
 */
export function parseHrBytes(bytes: number[]): { bpm: number; rrIntervals?: number[] } {
  if (bytes.length < 2) return { bpm: 0 };
  const flags = bytes[0];
  const bpm = bytes[1];
  const hasRR = (flags & 0x10) !== 0;
  const rrIntervals: number[] = [];
  if (hasRR && bytes.length > 2) {
    for (let i = 2; i <= bytes.length - 2; i += 2) {
      rrIntervals.push(((bytes[i] | (bytes[i + 1] << 8)) / 1024) * 1000);
    }
  }
  return { bpm, rrIntervals: rrIntervals.length > 0 ? rrIntervals : undefined };
}
