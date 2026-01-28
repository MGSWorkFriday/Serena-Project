/**
 * Filter om bij het scannen alleen Polar wearables te tonen.
 * - Naam bevat "Polar" (Polar H10, Polar H9, Polar Sense, Polar OH1, etc.)
 * - Of exacte modelnamen die soms zonder "Polar" adverteren: H10, H9, OH1, OH1+
 * - Geen naam / leeg: doorlaten (o.a. native scan met Polar-specifieke service-UUID)
 */
export function isPolarDevice(name: string | null | undefined): boolean {
  if (!name || typeof name !== 'string') return true;
  const n = name.trim();
  if (n === '') return true;
  if (n.toLowerCase().includes('polar')) return true;
  // Bekende Polar-modelnamen die soms zonder "Polar" in de advertentie staan
  if (/^(H10|H9|OH1\+?|OH1|Verity\s*Sense)$/i.test(n)) return true;
  return false;
}
