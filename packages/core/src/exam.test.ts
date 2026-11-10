import { describe, expect, it } from 'vitest';

import { Board, DEFAULT_RULES, examOpening, examOutcome, examTitle, levelExam, levelExamLabel, loadSnapshot, type Result } from './index';

const mk = (id: string, topic: string, level: number, format = 'choice') => ({
  id, topic, sub: `${topic}1`, level, kind: 'concept', prompt: id, format,
  choices: ['a', 'b', 'c'], answer: ['A'], key: ['k'],
});
const catalog = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'm',
      definition: {
        title: 'M', pass_ratio: 1, kinds: ['concept'],
        topic: [
          { slug: 't', tier: 1, title: 'Types', subs: ['t1'] },
          { slug: 'u', tier: 1, title: 'Units', subs: ['u1'] },
        ],
      },
      questions: [mk('a', 't', 0), mk('b', 't', 0), mk('c', 'u', 0), mk('d', 'u', 0, 'card')],
    },
  ],
} as never);
const b = Board.build(catalog, []);
const result = (q: Result['q'], correct: boolean): Result => ({ q, correct, guess: false, order: [0, 1, 2], picked: [], reply: '' });

describe('a level exam', () => {
  it('samples every open group at its level, and leaves open questions out', () => {
    expect(levelExam(b, 0, 10).questions.map((q) => q.id).sort()).toEqual(['a', 'b', 'c']);
  });

  it('names how many it asks of how many the level holds', () => {
    expect(levelExamLabel(DEFAULT_RULES, 0, 3, 10)).toBe('Start (3 of 3)');
    expect(levelExamLabel(DEFAULT_RULES, 1, 0, 10)).toBe('No unlocked Associate questions');
  });
});

describe("an exam's outcome", () => {
  const plan = levelExam(b, 0, 10, () => 0.5);
  const [qa, qb, qc] = ['a', 'b', 'c'].map((id) => catalog.questions.find((q) => q.id === id)!);
  const outcome = examOutcome(plan, [result(qa, true), result(qb, false), result(qc, true)], '2026-11-10T10:00:00Z', catalog.courses);

  it('scores it by topic, named by its title', () => {
    expect(outcome.byTopic).toEqual([
      { topic: 'm/t', title: 'Types', score: 1, n: 2 },
      { topic: 'm/u', title: 'Units', score: 1, n: 1 },
    ]);
    expect([outcome.score, outcome.n, outcome.percent]).toEqual([2, 3, 67]);
  });

  it('keeps the missed answers for their review', () => {
    expect(outcome.missed.map((r) => r.q.id)).toEqual(['b']);
  });

  it('stores every answer at the one moment the exam ended', () => {
    expect(new Set(outcome.attempts.map((a) => a.t))).toEqual(new Set(['2026-11-10T10:00:00Z']));
  });

  it('writes no certification record for a level exam', () => {
    expect(outcome.cert).toBeNull();
  });

  it("passes a certification's exam only where every question was answered", () => {
    const certPlan = { ...plan, cert: { course: 'm', id: 'm-t-foundation', passShare: 0.5 } };
    const stopped = examOutcome(certPlan, [result(qa, true), result(qb, true)], '2026-11-10T10:00:00Z', catalog.courses);
    expect(stopped.cert).toMatchObject({ score: 2, n: 3, passed: false });
  });
});

describe("an exam's title", () => {
  it('counts the question asked, then the misses reviewed', () => {
    expect(examTitle('ask', 0, 20, 0, 0)).toBe('Exam · 1 / 20');
    expect(examTitle('review', 0, 20, 1, 4)).toBe('Missed 2 / 4');
  });
});

describe('the exam opening', () => {
  it('opens on Associate across every module without a focus', () => {
    expect(examOpening(null)).toEqual({ course: null, level: 1 });
  });

  it("opens on the focus's module", () => {
    expect(examOpening({ course: 'python', topic: 'core', sub: null })).toEqual({ course: 'python', level: 1 });
  });

  it("takes a certification focus's level", () => {
    const f = { course: 'python', topic: 'core', sub: null, cert: 'python-core-professional' };
    expect(examOpening(f)).toEqual({ course: 'python', level: 2 });
  });
});
