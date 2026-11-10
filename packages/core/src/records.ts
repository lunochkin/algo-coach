import type { AttemptRecord, Grade, SessionRecord } from './types';

/** ISO-8601 UTC with seconds, as Python's datetime.now(UTC).isoformat(timespec="seconds"). */
export function isoNow(ms: number = Date.now()): string {
  return new Date(Math.floor(ms / 1000) * 1000).toISOString().replace('.000Z', '+00:00');
}

export function monthOf(t: string): string {
  return new Date(Date.parse(t)).toISOString().slice(0, 7);
}

export function attemptPath(device: string, t: string): string {
  return `progress/${device}/${monthOf(t)}.jsonl`;
}

export function sessionPath(device: string, t: string): string {
  return `progress/${device}/sessions/${monthOf(t)}.jsonl`;
}

export function statusPath(device: string, t: string): string {
  return `progress/${device}/status/${monthOf(t)}.jsonl`;
}

export function focusPath(device: string, t: string): string {
  return `progress/${device}/focus/${monthOf(t)}.jsonl`;
}

export function certPath(device: string, t: string): string {
  return `progress/${device}/certs/${monthOf(t)}.jsonl`;
}

export function isCertFile(path: string): boolean {
  return /^progress\/[^/]+\/certs\/[^/]+\.jsonl$/.test(path);
}

export function lessonPath(device: string, t: string): string {
  return `progress/${device}/lessons/${monthOf(t)}.jsonl`;
}

export function isLessonFile(path: string): boolean {
  return /^progress\/[^/]+\/lessons\/[^/]+\.jsonl$/.test(path);
}

export function isFocusFile(path: string): boolean {
  return /^progress\/[^/]+\/focus\/[^/]+\.jsonl$/.test(path);
}

export function isStatusFile(path: string): boolean {
  return /^progress\/[^/]+\/status\/[^/]+\.jsonl$/.test(path);
}

/** Exactly progress/<device>/*.jsonl; sessions/, status/ and focus/ subfolders are not attempts. */
export function isAttemptFile(path: string): boolean {
  return /^progress\/[^/]+\/[^/]+\.jsonl$/.test(path);
}

export function isSessionFile(path: string): boolean {
  return /^progress\/[^/]+\/sessions\/[^/]+\.jsonl$/.test(path);
}

export function makeAttempt(
  t: string,
  course: string,
  id: string,
  ok: boolean,
  guess: boolean,
  grade?: Grade,
  card?: CardFields,
): AttemptRecord {
  const rec: AttemptRecord = { t, course, id, ok };
  if (guess) rec.guess = true;
  if (grade) rec.grade = grade;
  if (card?.missed) rec.missed = card.missed;
  if (card?.traps) rec.traps = card.traps;
  if (card?.wrong) rec.wrong = true;
  return rec;
}

export interface CardFields {
  grade: Grade;
  missed?: number[];
  traps?: number[];
  wrong?: true;
}

export function gradeCard(points: number, recalled: Set<number>, traps: Set<number>, wrong: boolean): Grade {
  if (recalled.size === 0) return 'n';
  return recalled.size < points || traps.size > 0 || wrong ? 'p' : 'k';
}

/** The card part of an attempt record; empty lists and false are omitted. */
export function cardFields(
  points: number,
  recalled: Set<number>,
  traps: Set<number>,
  wrong: boolean,
): CardFields {
  const out: CardFields = { grade: gradeCard(points, recalled, traps, wrong) };
  const missed = Array.from({ length: points }, (_, i) => i).filter((i) => !recalled.has(i));
  if (missed.length) out.missed = missed;
  if (traps.size) out.traps = [...traps].sort((a, b) => a - b);
  if (wrong) out.wrong = true;
  return out;
}

/** "Knew 3/3", "Partly 3/3 · wrong claim", "Partly 2/3", "Didn't 0/3". */
export function cardLabel(points: number, recalled: Set<number>, traps: Set<number>, wrong: boolean): string {
  const word = { k: 'Knew', p: 'Partly', n: "Didn't" }[gradeCard(points, recalled, traps, wrong)];
  const extra = recalled.size && (traps.size || wrong) ? ' · wrong claim' : '';
  return `${word} ${recalled.size}/${points}${extra}`;
}

/** Python json.dumps of a flat dict: ", " and ": " separators, non-ASCII escaped. */
export function pyJson(rec: object): string {
  const parts = Object.entries(rec).map(([k, v]) => `${asciiJson(k)}: ${asciiJson(v)}`);
  return `{${parts.join(', ')}}`;
}

function asciiJson(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(asciiJson).join(', ')}]`;
  return JSON.stringify(v).replace(
    /[\u007f-￿]/g,
    (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`,
  );
}

export function parseLines<T>(text: string): T[] {
  return text
    .split('\n')
    .filter((l) => l)
    .map((l) => JSON.parse(l) as T);
}

export function isSessionRecord(r: unknown): r is SessionRecord {
  return typeof r === 'object' && r !== null && 'mode' in r && 'score' in r;
}
