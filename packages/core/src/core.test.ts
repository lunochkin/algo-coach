import { describe, expect, it } from 'vitest';

import {
  answerKey,
  sections,
  DEFAULT_FSRS,
  DEFAULT_RULES,
  type Question,
  levelName,
  type Snapshot,
  cardFields,
  cardLabel,
  makeAttempt,
  isAttemptFile,
  isFocusFile,
  isSessionFile,
  isStatusFile,
  statusPath,
  Board,
  byTopic,
  loadSnapshot,
  drillQueue,
  selectExam,
  block,
  decodeBase64,
  encodeBase64,
  gradeChoice,
  hasAnswer,
  isoNow,
  nextReminderAt,
  parseQuestion,
  pyJson,
} from './index';

describe('records', () => {
  it('formats timestamps and lines like Python', () => {
    expect(isoNow(Date.UTC(2026, 0, 5, 9, 0, 0, 750))).toBe('2026-01-05T09:00:00+00:00');
    expect(pyJson({ t: 'x', course: 'py', id: 'é', ok: true, guess: true })).toBe(
      '{"t": "x", "course": "py", "id": "\\u00e9", "ok": true, "guess": true}',
    );
  });
});

describe('base64', () => {
  it('round-trips UTF-8', () => {
    for (const s of ['', 'a', 'ab', 'abc', 'naïve → ok 🙂\n']) {
      expect(decodeBase64(encodeBase64(s))).toBe(s);
    }
    expect(encodeBase64('héllo')).toBe(Buffer.from('héllo').toString('base64'));
    expect(decodeBase64('aGVs\nbG8=\n')).toBe('hello');
  });
});

describe('choices', () => {
  const q = parseQuestion(
    { id: 'x', topic: 't', sub: 's', kind: 'k', prompt: 'p', choices: ['a', 'b', 'c'], answer: ['A', 'C'] },
    'c',
  );
  it('grades by displayed position', () => {
    const order = [2, 0, 1]; // displayed A=c, B=a, C=b
    expect(answerKey(q, order)).toBe('AB');
    expect(gradeChoice(q, order, [1, 0])).toBe(true);
    expect(gradeChoice(q, order, [0])).toBe(false);
    expect(gradeChoice(q, order, [0, 1, 2])).toBe(false);
  });
  it('rejects empty replies', () => {
    expect(hasAnswer(' ?? ')).toBe(false);
    expect(hasAnswer('a?')).toBe(true);
  });
});

describe('display', () => {
  it('dedents and strips', () => {
    expect(block('\n    a\n      b\n\n    c\n')).toBe('a\n  b\n\nc');
  });
});

describe('reminder', () => {
  it('picks the next reminder hour at or after a time', () => {
    const t = new Date(2026, 0, 5, 8, 30).getTime();
    expect(nextReminderAt(t, 9)).toBe(new Date(2026, 0, 5, 9).getTime());
    expect(nextReminderAt(new Date(2026, 0, 5, 9).getTime(), 9)).toBe(new Date(2026, 0, 5, 9).getTime());
    expect(nextReminderAt(new Date(2026, 0, 5, 9, 1).getTime(), 9)).toBe(new Date(2026, 0, 6, 9).getTime());
  });
});

describe('modes', () => {
  const mk = (id: string, topic: string, level = 1, format: 'choice' | 'card' = 'choice') => ({
    id,
    topic,
    sub: 's',
    level,
    kind: 'k',
    prompt: id,
    format,
    choices: ['a', 'b', 'c'],
    answer: ['A'],
  });
  const cat = loadSnapshot({
    format: 2,
    courses: [
      {
        slug: 'c',
        definition: {
          title: 'C',
          pass_ratio: 1,
          kinds: ['k'],
          topic: [
            { slug: 't', tier: 1, title: 'T', subs: ['s'] },
            { slug: 'u', tier: 1, title: 'U', subs: ['s'] },
          ],
        },
        questions: [mk('a', 't'), mk('b', 't'), mk('c', 't'), mk('d', 'u'), mk('e', 'u', 1, 'card')],
      },
    ],
  });
  const b = Board.build(cat, []);
  it('samples min(n, pool) exam questions without cards or repeats', () => {
    const qs = selectExam(b, 1, 3);
    expect(qs).toHaveLength(3);
    expect(new Set(qs.map((q) => q.id)).size).toBe(3);
    expect(qs.some((q) => q.format === 'card')).toBe(false);
    expect(selectExam(b, 1, 40)).toHaveLength(4);
  });
  it('drill picks from its scope and scores per topic in first-seen order', () => {
    expect((drillQueue(b, { course: 'c', topic: 't' }, 10).pick(b, 0) as Question).topic).toBe('t');
    const [a, , , d] = cat.questions;
    expect(
      byTopic([
        { q: d, correct: true },
        { q: a, correct: false },
        { q: d, correct: false },
      ]),
    ).toEqual([
      { topic: 'c/u', score: 1, n: 2 },
      { topic: 'c/t', score: 0, n: 1 },
    ]);
  });
});

describe('data repo files', () => {
  it('classifies attempts, sessions and status logs', () => {
    expect(isAttemptFile('progress/phone/2026-11.jsonl')).toBe(true);
    expect(isAttemptFile('progress/phone/status/2026-11.jsonl')).toBe(false);
    expect(isAttemptFile('progress/phone/sessions/2026-11.jsonl')).toBe(false);
    expect(isStatusFile('progress/laptop/status/2026-11.jsonl')).toBe(true);
    expect(isAttemptFile('progress/phone/focus/2026-11.jsonl')).toBe(false);
    expect(isFocusFile('progress/phone/focus/2026-11.jsonl')).toBe(true);
    expect(isSessionFile('progress/laptop/status/2026-11.jsonl')).toBe(false);
    expect(statusPath('phone', '2026-11-07T01:00:00+00:00')).toBe('progress/phone/status/2026-11.jsonl');
  });
});

describe('card records', () => {
  it('labels grades and writes Python-style lists', () => {
    expect(cardLabel(3, new Set([0, 1, 2]), new Set(), false)).toBe('Knew 3/3');
    expect(cardLabel(3, new Set([0, 1, 2]), new Set([0]), false)).toBe('Partly 3/3 · wrong claim');
    expect(cardLabel(3, new Set([0, 1]), new Set(), false)).toBe('Partly 2/3');
    expect(cardLabel(3, new Set(), new Set([1]), true)).toBe("Didn't 0/3");
    const card = cardFields(3, new Set([0]), new Set([1]), true);
    expect(pyJson(makeAttempt('t', 'c', 'q', false, false, card.grade, card))).toBe(
      '{"t": "t", "course": "c", "id": "q", "ok": false, "grade": "p", "missed": [1, 2], "traps": [1], "wrong": true}',
    );
  });
});

describe('snapshot formats', () => {
  it('reads a format 2 snapshot with built-in FSRS settings', () => {
    const cat = loadSnapshot({
      format: 2,
      rules: { intervals_days: [1, 3], mastered_box: 4, levels: { '1': 'Associate' } },
      courses: [],
    } as unknown as Snapshot);
    expect(cat.rules.fsrs).toEqual(DEFAULT_FSRS);
    expect(cat.rules.levels).toEqual(DEFAULT_RULES.levels);
    expect(levelName(cat.rules, 0)).toBe('Foundation');
    expect(levelName(cat.rules, 2, true)).toBe('Prof.');
  });
});

describe('lesson sections', () => {
  it('cuts at headings outside code fences and keeps the text', () => {
    const md = '# T\nintro\n## One\na\n```\n## not\n```\n### Two!\nb';
    const got = sections(md);
    expect(got.map((s) => s.anchor)).toEqual([null, 'one', 'two']);
    expect(got.map((s) => s.text).join('\n')).toBe(md);
  });
});
