import { certQuestions, certStates, type CertRecord } from './certs';
import { groupKey } from './courses';
import { dayName } from './forecast';
import type { Focus } from './focus';
import { GOOD, replay, type Memory } from './fsrs';
import { dayStart, focusScope, newToday } from './queue';
import { passed, type Board } from './schedule';
import type { Attempt, FsrsRules, Question } from './types';
import { targetLine } from './words/home';

const DAY = 86_400_000;
export const PACE_DAYS = 14;
// past this a date says nothing a reader plans by
const HORIZON_DAYS = 3 * 365;
const EARNED = ['earned', 'needs_refresh', 'empty'];

/** Whether the focus is reached, as the route and the projection read it: `knowledge.md`, Projections. */
export function targetReached(b: Board, f: Focus, exams: CertRecord[]): boolean {
  const c = b.course(f.course);
  if (!c) return false;
  if (f.cert) return EARNED.includes(certStates(b, c, exams).get(f.cert)?.state ?? '');
  return groupsOf(b, f).every((qs) => b.done(qs[0]));
}

function groupsOf(b: Board, f: Focus): Question[][] {
  const groups = new Map<string, Question[]>();
  for (const q of focusScope(b, f)) {
    const k = groupKey(q);
    groups.set(k, [...(groups.get(k) ?? []), q]);
  }
  return [...groups.values()];
}

/** New questions the focus still needs first answered: a failed one is taken to pass on review. */
export function newNeeded(b: Board, f: Focus): number {
  const x = f.cert ? b.course(f.course)?.certs?.get(f.cert) : undefined;
  // a certification's own level is covered at its rule's ratio, as `certStates` reads it
  const ratio = (q: Question) =>
    x?.rule.coverageRatio != null && q.level === x.level ? x.rule.coverageRatio : b.ratio(q);
  let n = 0;
  for (const qs of groupsOf(b, f)) {
    const need = Math.ceil(ratio(qs[0]) * qs.length) - qs.filter((q) => passed(b.attempts(q))).length;
    const seen = qs.filter((q) => b.attempts(q).length && !passed(b.attempts(q))).length;
    n += Math.max(0, need - seen);
  }
  return n;
}

/** New questions first answered per day over the last complete learning days, or null with no such day. */
export function realPace(b: Board, now: number, offsetMinutes?: number): number | null {
  const today = dayStart(now, offsetMinutes);
  let first = Infinity;
  let n = 0;
  for (const h of b.hist.values()) {
    if (!h.length) continue;
    first = Math.min(first, h[0].t);
    if (h[0].t >= today - PACE_DAYS * DAY && h[0].t < today) n++;
  }
  const days = Math.min(PACE_DAYS, Math.floor((today - dayStart(first, offsetMinutes)) / DAY));
  return days > 0 ? n / days : null;
}

/** The day `need` new questions are done at `perDay`, `todayLeft` of them still open today. */
function dayFor(need: number, perDay: number, todayLeft: number, today: number): number | null {
  if (need <= todayLeft) return today;
  if (perDay <= 0) return null;
  const days = Math.ceil((need - todayLeft) / perDay);
  return days > HORIZON_DAYS ? null : today + days * DAY;
}

/** When a question's stability first reaches `days`, every review passing; `from` is a fresh question's first answer. */
function stableAt(
  attempts: Attempt[],
  memory: Memory | null,
  days: number,
  rules: FsrsRules,
  from: number,
): number | null {
  const seq = [...attempts];
  let mem = memory;
  if (!mem) {
    seq.push({ t: from, rating: GOOD });
    mem = replay(seq, rules);
  }
  const end = from + HORIZON_DAYS * DAY;
  while (mem && mem.stability < days) {
    const t = Math.max(mem.due, from);
    if (t > end) return null;
    seq.push({ t, rating: GOOD });
    mem = replay(seq, rules);
  }
  return mem ? (seq.at(-1)?.t ?? from) : null;
}

/** The day a certification's retention holds, its unseen questions first answered on the day coverage does. */
function retainedDay(b: Board, f: Focus, covered: number, now: number, offsetMinutes?: number): number | null {
  const c = b.course(f.course);
  const x = f.cert ? c?.certs?.get(f.cert) : undefined;
  if (!c || !x) return covered;
  const qs = certQuestions(b, c, x);
  const k = Math.ceil(x.rule.share * qs.length);
  if (!k) return covered;
  const times = qs
    .map((q) => {
      const seen = b.attempts(q).length > 0;
      return stableAt(
        b.attempts(q),
        b.memory(q),
        x.rule.stabilityDays,
        b.rules.fsrs,
        seen ? now : Math.max(covered, now),
      );
    })
    .filter((t): t is number => t !== null)
    .sort((p, q) => p - q);
  if (times.length < k) return null;
  return Math.max(covered, dayStart(Math.max(now, times[k - 1]), offsetMinutes));
}

export interface TargetDate {
  perDay: number;
  day: number | null; // null: past the horizon, or no pace to reach it at
}

export interface TargetProjection {
  reached: boolean;
  atLimit: TargetDate;
  atPace: TargetDate | null; // null: no complete learning day in the log yet
}

/** When the focus is reached at the daily limit and at the user's own pace. */
export function projectTarget(
  b: Board,
  f: Focus,
  exams: CertRecord[],
  pace: { perDay: number; limit: number },
  now: number,
  offsetMinutes?: number,
): TargetProjection {
  const today = dayStart(now, offsetMinutes);
  const reached = targetReached(b, f, exams);
  const need = newNeeded(b, f);
  const done = newToday(b, now, offsetMinutes);
  const at = (perDay: number, todayLeft: number): TargetDate => {
    if (reached) return { perDay, day: today };
    const covered = dayFor(need, perDay, Math.max(0, todayLeft), today);
    const day = covered === null ? null : f.cert ? retainedDay(b, f, covered, now, offsetMinutes) : covered;
    return { perDay, day };
  };
  const real = realPace(b, now, offsetMinutes);
  return {
    reached,
    atLimit: at(pace.perDay, pace.limit - done),
    atPace: real === null ? null : at(real, real - done),
  };
}

/** The focus panel's line naming when the focus is reached, or null once it is. */
export function targetView(p: TargetProjection, now: number, offsetMinutes?: number): string | null {
  if (p.reached) return null;
  const today = dayStart(now, offsetMinutes);
  const name = (d: TargetDate) => (d.day === null ? null : d.day === today ? 'today' : dayName(d.day, offsetMinutes));
  return targetLine(
    { perDay: p.atLimit.perDay, day: name(p.atLimit) },
    p.atPace && { perDay: p.atPace.perDay, day: name(p.atPace) },
  );
}
