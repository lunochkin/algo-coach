import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import {
  Board,
  certFocus,
  loadSnapshot,
  newNeeded,
  projectTarget,
  realPace,
  targetReached,
  targetView,
  type AttemptRecord,
  type Focus,
  type Snapshot,
} from './index';

const mk = (id: string) => ({
  id,
  topic: 't',
  sub: 's',
  level: 0,
  kind: 'concept',
  prompt: id,
  format: 'choice' as const,
  choices: ['a', 'b', 'c'],
  answer: ['A'],
});
const ids = Array.from({ length: 10 }, (_, i) => `q${i}`);
const snapshot = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'a',
      definition: {
        title: 'A',
        pass_ratio: 1,
        kinds: ['concept'],
        topic: [{ slug: 't', tier: 1, title: 'T', subs: ['s'] }],
      },
      questions: ids.map(mk),
    },
  ],
} as never);
const UTC = 0;
const NOW = Date.parse('2026-11-10T12:00:00.000Z');
const FOCUS: Focus = { course: 'a', topic: null, sub: null };
const at = (iso: string, id: string, ok = true): AttemptRecord => ({ t: iso, course: 'a', id, ok });
const build = (records: AttemptRecord[]) => Board.build(snapshot, records, null, 'a');
const day = (iso: string) => Date.parse(`${iso}T04:00:00.000Z`);

describe("a focus's remaining work", () => {
  it('counts every unpassed question at a pass ratio of one', () => {
    expect(newNeeded(build([]), FOCUS)).toBe(10);
  });

  it('takes a failed question to pass on review, so it needs no new slot', () => {
    const b = build([at('2026-11-09T08:00:00.000Z', 'q0', false), at('2026-11-09T08:00:00.000Z', 'q1')]);
    expect(newNeeded(b, FOCUS)).toBe(8);
  });

  it('reads a focus with every group done as reached', () => {
    const b = build(ids.map((id) => at('2026-11-09T08:00:00.000Z', id)));
    expect(targetReached(b, FOCUS, [])).toBe(true);
    expect(targetView(projectTarget(b, FOCUS, [], { perDay: 10, limit: 10 }, NOW, UTC), NOW, UTC)).toBeNull();
  });
});

describe('the pace', () => {
  it('has none before a complete learning day', () => {
    expect(realPace(build([at('2026-11-10T08:00:00.000Z', 'q0')]), NOW, UTC)).toBeNull();
  });

  it('counts first answers over the days since the log began, at most fourteen', () => {
    const b = build([
      at('2026-11-08T08:00:00.000Z', 'q0'),
      at('2026-11-09T08:00:00.000Z', 'q1'),
      at('2026-11-09T09:00:00.000Z', 'q2'),
    ]);
    expect(realPace(b, NOW, UTC)).toBe(1.5);
  });

  it('reads a day with no answer as zero', () => {
    const b = build([at('2026-10-01T08:00:00.000Z', 'q0'), at('2026-11-09T08:00:00.000Z', 'q1')]);
    expect(realPace(b, NOW, UTC)).toBe(1 / 14);
  });
});

describe("the focus's date", () => {
  it("spends today's room first, then the daily limit", () => {
    const p = projectTarget(build([]), FOCUS, [], { perDay: 4, limit: 4 }, NOW, UTC);
    expect(p.atLimit.day).toBe(day('2026-11-12')); // 4 today, 4 tomorrow, 2 the day after
  });

  it('names both dates on one line', () => {
    const b = build([at('2026-11-08T08:00:00.000Z', 'q0'), at('2026-11-09T08:00:00.000Z', 'q1')]);
    const line = targetView(projectTarget(b, FOCUS, [], { perDay: 8, limit: 8 }, NOW, UTC), NOW, UTC);
    expect(line).toBe('at 8 a day, by today · at your pace of 1 a day, by Tue 17 Nov');
  });

  it('says never at a pace of zero', () => {
    const b = build([at('2026-10-01T08:00:00.000Z', 'q0', false)]);
    const line = targetView(projectTarget(b, FOCUS, [], { perDay: 0, limit: 0 }, NOW, UTC), NOW, UTC);
    expect(line).toBe('at 0 a day, never · at your pace of 0 a day, never');
  });
});

const fixtures = JSON.parse(
  readFileSync(resolve(__dirname, '../../../tests/fixtures/knowledge/scheduling.json'), 'utf8'),
);
const named = (name: string) => {
  const f = fixtures.cert_states.find((x: { name: string }) => x.name === name);
  const cat = loadSnapshot({ format: 6, courses: f.courses } as Snapshot);
  return { c: cat.courses[0], b: Board.build(cat, f.records), exams: f.exams ?? [], cat };
};

describe("a certification's date", () => {
  it('waits for retention after coverage, so it falls later than coverage alone', () => {
    const { c, cat } = named('nothing done');
    const id = c.certs!.certs.find((x) => x.certified)!.id;
    const focus = certFocus(c, id, false)!;
    const b = Board.build(cat, [], null, c.slug);
    const cert = projectTarget(b, focus, [], { perDay: 1000, limit: 1000 }, NOW, UTC);
    // the limit covers every group today, and stability takes reviews days apart to reach the rule's
    expect(cert.atLimit.day).toBeGreaterThan(day('2026-11-10'));
  });
});
