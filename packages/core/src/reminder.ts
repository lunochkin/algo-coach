import { type Board } from './schedule';

/** Earliest time at which some seen question, locked group or not, is ready to review; null if none. */
export function earliestReview(b: Board, now: number): number | null {
  let best: number | null = null;
  for (const qs of b.servedGroups()) {
    for (const q of qs) {
      const a = b.attempts(q);
      if (!a.length) continue;
      // Weak and due questions are served once FSRS's due has come; so are the rest, later.
      const at = Math.max(now, b.memory(q)?.due ?? now);
      if (best === null || at < best) best = at;
    }
  }
  return best === null ? null : Math.max(best, now);
}

/** First local time hour:00 at or after `t`. */
export function nextReminderAt(t: number, hour: number): number {
  const d = new Date(t);
  d.setHours(hour, 0, 0, 0);
  if (d.getTime() < t) d.setDate(d.getDate() + 1);
  return d.getTime();
}

export function reviewCount(b: Board, at: number): number {
  let n = 0;
  for (const qs of b.servedGroups()) {
    for (const q of qs) {
      if (b.toReview(q, at)) n++;
    }
  }
  return n;
}
