/**
 * UQ-FI-2 (D-UQFI.4): one gap line per section. Pure grouping: a section's repeated
 * "not available / not assessed / no assessment" statements become one line naming every
 * subject it applies to. The fact is stated once, never re-worded, softened or merged with a
 * different fact (D-E5.46): items group only on an exact (fact, reason) match. Nothing here
 * composes words; the fact and the subjects are the server's or the page's own strings.
 */
export interface GapItem {
  /** What the fact applies to (a block title, a field label), in the page's existing words. */
  subject: string;
  /** The gap statement, exactly as the page shows it today. */
  fact: string;
  /** An optional reason code; two items with the same words but different reasons never merge. */
  reason?: string;
  /** The catalogued gap id (MissingClaim), carried onto the subject so no gap id is lost. */
  gapId?: string;
}

export interface GapGroupLine {
  fact: string;
  reason?: string;
  subjects: { subject: string; gapId?: string }[];
}

/** D-E5.46 precedence: no readings, conflicting, not enough, not analysed yet, still processing. */
const PRECEDENCE_CODES = ["NO_READINGS", "READINGS_CONFLICT", "NOT_ENOUGH_READINGS", "NOT_ANALYSED", "PROCESSING"];
const PRECEDENCE_WORDS = [/\bno readings\b/i, /\bconflict/i, /\bnot enough readings\b/i, /\bnot analysed yet\b/i, /\bstill processing\b/i];

function rank(line: GapGroupLine): number {
  const byCode = line.reason === undefined ? -1 : PRECEDENCE_CODES.indexOf(line.reason);
  if (byCode >= 0) return byCode;
  const byWords = PRECEDENCE_WORDS.findIndex((re) => re.test(line.fact));
  return byWords >= 0 ? byWords : PRECEDENCE_CODES.length;
}

export function groupGaps(items: readonly GapItem[]): GapGroupLine[] {
  const lines: GapGroupLine[] = [];
  const byKey = new Map<string, GapGroupLine>();
  for (const item of items) {
    const key = JSON.stringify([item.fact, item.reason ?? null]);
    let line = byKey.get(key);
    if (!line) {
      line = item.reason === undefined ? { fact: item.fact, subjects: [] } : { fact: item.fact, reason: item.reason, subjects: [] };
      byKey.set(key, line);
      lines.push(line);
    }
    line.subjects.push(item.gapId === undefined ? { subject: item.subject } : { subject: item.subject, gapId: item.gapId });
  }
  // A stable sort: the precedence facts first in D-E5.46 order, every other fact in first-seen order.
  return lines.map((line, i) => ({ line, i })).sort((a, b) => rank(a.line) - rank(b.line) || a.i - b.i).map((x) => x.line);
}
