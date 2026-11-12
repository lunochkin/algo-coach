import { describe, expect, it } from 'vitest';

import { Board, forecastView, loadSnapshot, reviewForecast, withStatuses, type AttemptRecord } from './index';

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
const module = (slug: string) => ({
  slug,
  definition: {
    title: slug.toUpperCase(),
    pass_ratio: 1,
    kinds: ['concept'],
    topic: [{ slug: 't', tier: 1, title: 'T', subs: ['s'] }],
  },
  questions: [mk('q1'), mk('q2')],
});
const snapshot = loadSnapshot({ format: 6, courses: [module('a'), module('b')] } as never);
const UTC = 0;
const NOW = Date.parse('2026-11-10T12:00:00.000Z');
const at = (iso: string, course: string, id: string, ok: boolean): AttemptRecord => ({ t: iso, course, id, ok });
const total = (b: Board) => reviewForecast(b, NOW, 14, UTC).reduce((n, d) => n + d.reviews, 0);

describe('the review forecast', () => {
  it('reads fourteen learning days, the first holding now', () => {
    const days = reviewForecast(Board.build(snapshot, []), NOW, 14, UTC);
    expect(days).toHaveLength(14);
    expect(days[0].start).toBe(Date.parse('2026-11-10T04:00:00.000Z'));
    expect(days.every((d) => d.reviews === 0)).toBe(true);
  });

  it('counts an overdue review on the first day', () => {
    const b = Board.build(snapshot, [at('2026-11-10T08:00:00.000Z', 'a', 'q1', false)]);
    expect(reviewForecast(b, NOW, 14, UTC)[0].reviews).toBeGreaterThanOrEqual(1);
  });

  it('projects the reviews after a pass, at growing intervals', () => {
    const b = Board.build(snapshot, [at('2026-11-10T08:00:00.000Z', 'a', 'q1', true)]);
    const days = reviewForecast(b, NOW, 14, UTC).map((d) => d.reviews);
    expect(days[0]).toBe(1); // the ten-minute step, overdue by now
    const later = days.flatMap((n, i) => (i > 0 && n ? [i] : []));
    expect(later.length).toBeGreaterThanOrEqual(2);
    expect(later[1] - later[0]).toBeGreaterThan(later[0]);
  });

  it('counts nothing for a question due past the horizon', () => {
    const long = ['2026-01-01', '2026-01-04', '2026-01-20', '2026-03-01', '2026-07-01'].map((d) =>
      at(`${d}T08:00:00.000Z`, 'a', 'q1', true),
    );
    const b = Board.build(snapshot, [at('2025-12-31T08:00:00.000Z', 'a', 'q1', true), ...long]);
    const due = b.memory(b.questions()[0])!.due;
    expect(due).toBeGreaterThan(NOW + 14 * 86_400_000);
    expect(total(b)).toBe(0);
  });

  it("leaves out a paused module's questions, as the review queue does", () => {
    const paused = withStatuses(snapshot, [{ t: '2026-11-01T00:00:00.000Z', course: 'b', status: 'paused' }]);
    const records = [at('2026-11-10T08:00:00.000Z', 'b', 'q1', false)];
    expect(total(Board.build(snapshot, records))).toBeGreaterThan(0);
    expect(total(Board.build(paused, records))).toBe(0);
  });
});

describe("the forecast's reading", () => {
  const days = [3, 0, 7, 7].map((reviews, i) => ({
    start: Date.parse('2026-11-10T04:00:00.000Z') + i * 86_400_000,
    reviews,
  }));

  it('names today, then each day by its date', () => {
    const v = forecastView(days, UTC);
    expect(v.bars.map((b) => b.day)).toEqual(['Today', 'Wed 11 Nov', 'Thu 12 Nov', 'Fri 13 Nov']);
    expect(v.last).toBe('Fri 13 Nov');
  });

  it('labels today and the first busiest day alone', () => {
    const v = forecastView(days, UTC);
    expect(v.bars.map((b) => b.labelled)).toEqual([true, false, true, false]);
    expect(v.max).toBe(7);
    expect(v.summary).toBe('17 over 4 days · 3 today');
  });
});
