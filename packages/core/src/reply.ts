import { LETTERS } from './courses';
import type { Question } from './types';

// Characters Python's str.isspace() accepts; JS \s differs (it adds U+FEFF, lacks U+001C-U+001F, U+0085).
const WS = '\\t\\n\\v\\f\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000';
const WS_ALL = new RegExp(`[${WS}]+`, 'g');
const WS_EDGES = new RegExp(`^[${WS}]+|[${WS}]+$`, 'g');
const QUOTE_EDGES = /^[`'"]+|[`'"]+$/g;

export function pyStrip(text: string): string {
  return text.replace(WS_EDGES, '');
}

/** Python: "".join(text.strip().strip("`'\"").split()), lowercased unless case-sensitive. */
export function normalize(text: string, caseSensitive: boolean): string {
  const t = pyStrip(text).replace(QUOTE_EDGES, '').replace(WS_ALL, '');
  return caseSensitive ? t : t.toLowerCase();
}

/** A reply ending in `?` is a guess. */
export function splitGuess(reply: string): [string, boolean] {
  const r = pyStrip(reply);
  return r.endsWith('?') ? [r.slice(0, -1), true] : [r, false];
}

/** True when the reply carries an answer, i.e. is not empty after dropping `?`s. */
export function hasAnswer(raw: string): boolean {
  return pyStrip(raw).replace(/\?+$/, '') !== '';
}

export function matchShort(reply: string, q: Pick<Question, 'accept' | 'caseSensitive'>): boolean {
  const r = normalize(reply, q.caseSensitive);
  return q.accept.some((a) => normalize(a, q.caseSensitive) === r);
}

/** Random display order: displayed position -> choice index. */
export function choiceOrder(n: number, rng: () => number = Math.random): number[] {
  const a = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** Picked displayed positions are correct iff they map exactly onto the answer set. */
export function gradeChoice(q: Question, order: number[], picked: number[]): boolean {
  const expected = new Set(q.answer.map((i) => order.indexOf(i)));
  const got = new Set(picked);
  return got.size === expected.size && [...got].every((p) => expected.has(p));
}

/** Answer letters in displayed order, e.g. "AC". */
export function answerKey(q: Question, order: number[]): string {
  return q.answer
    .map((i) => order.indexOf(i))
    .sort((a, b) => a - b)
    .map((p) => LETTERS[p])
    .join('');
}

/** textwrap.dedent(text).strip(), for display. */
export function block(text: string): string {
  const lines = text.split('\n');
  let margin: string | null = null;
  for (const line of lines) {
    if (line.trim() === '') continue;
    const indent = /^[ \t]*/.exec(line)![0];
    if (margin === null || !indent.startsWith(margin)) {
      margin = margin === null ? indent : commonPrefix(margin, indent);
    }
  }
  const m = margin ?? '';
  return lines
    .map((l) => (l.trim() === '' ? '' : l.slice(m.length)))
    .join('\n')
    .trim();
}

function commonPrefix(a: string, b: string): string {
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  return a.slice(0, i);
}

/** One run of authored prose: code where the author wrote backticks. */
export interface Span {
  text: string;
  code: boolean;
}

/** Authored prose split at its backtick pairs, as a lesson renders inline code. A lone backtick stays text. */
export function spans(text: string): Span[] {
  const out: Span[] = [];
  let at = 0;
  for (const m of text.matchAll(/`([^`\n]+)`/g)) {
    if (m.index > at) out.push({ text: text.slice(at, m.index), code: false });
    out.push({ text: m[1], code: true });
    at = m.index + m[0].length;
  }
  if (at < text.length) out.push({ text: text.slice(at), code: false });
  return out;
}
