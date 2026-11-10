import { describe, expect, it } from 'vitest';

import {
  answerResult,
  Board,
  canSubmit,
  ExamRun,
  flipped,
  gradeResult,
  loadSnapshot,
  NEW_STEP,
  nextQueue,
  QueueRun,
  reviewQueue,
  togglePick,
  type AttemptRecord,
  type Question,
  type Result,
} from './index';

const mk = (id: string, format = 'choice') => ({
  id,
  topic: 't',
  sub: 's',
  level: 0,
  kind: 'k',
  prompt: id,
  format,
  choices: ['a', 'b', 'c'],
  answer: ['A'],
  accept: ['yes'],
  key: ['one', 'two'],
});
const catalog = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'c',
      definition: { title: 'C', pass_ratio: 1, kinds: ['k'], topic: [{ slug: 't', tier: 1, title: 'T', subs: ['s'] }] },
      questions: [mk('a'), mk('b'), mk('s', 'short'), mk('o', 'card')],
    },
  ],
} as never);
const q = (id: string): Question => catalog.questions.find((x) => x.id === id)!;
const reply = (o: Partial<{ text: string; picked: number[]; guessing: boolean }>) => ({
  text: '',
  picked: [],
  guessing: false,
  ...o,
});
const result = (x: Question, correct: boolean): Result => ({
  q: x,
  correct,
  guess: false,
  order: [0, 1, 2],
  picked: [],
  reply: '',
});

describe('one answer', () => {
  it('reads a short reply ending in ? as a guess, and matches the rest', () => {
    const r = answerResult(q('s'), [], reply({ text: 'yes?' }));
    expect(r).toMatchObject({ correct: true, guess: true, reply: 'yes' });
  });

  it('grades a choice by the displayed positions picked', () => {
    // displayed first is choice index 2, which is not the answer
    expect(answerResult(q('a'), [2, 0, 1], reply({ picked: [1] })).correct).toBe(true);
    expect(answerResult(q('a'), [2, 0, 1], reply({ picked: [0] })).correct).toBe(false);
  });

  it('grades an open question correct only on every point and nothing wrong', () => {
    expect(gradeResult(q('o'), [], new Set([0, 1]), new Set(), false)).toMatchObject({ correct: true, grade: 'k' });
    expect(gradeResult(q('o'), [], new Set([0, 1]), new Set(), true)).toMatchObject({ correct: false, grade: 'p' });
  });

  it('replaces the pick on a single answer, and toggles it on several', () => {
    expect(togglePick([0], 2, false)).toEqual([2]);
    expect(togglePick([0, 2], 2, true)).toEqual([0]);
    expect(togglePick([0], 2, true)).toEqual([0, 2]);
  });

  it('submits a short reply once it holds text, and a choice once something is picked', () => {
    expect(canSubmit(q('s'), reply({ text: '  ' }))).toBe(false);
    expect(canSubmit(q('s'), reply({ text: 'x' }))).toBe(true);
    expect(canSubmit(q('a'), reply({}))).toBe(false);
    expect(canSubmit(q('a'), reply({ picked: [1] }))).toBe(true);
  });

  it('flips one tick without touching the set it was given', () => {
    const s = new Set([1]);
    expect([...flipped(s, 0)].sort()).toEqual([0, 1]);
    expect([...flipped(s, 1)]).toEqual([]);
    expect([...s]).toEqual([1]);
  });
});

describe('a queue run', () => {
  const held = (attempts: AttemptRecord[] = []) => ({ catalog, attempts });
  const run = (limit: number) => new QueueRun(nextQueue(Board.build(catalog, []), limit), 'next', null, null, held());

  it('picks a question at the start, fresh where it was never answered', () => {
    const r = run(1);
    expect(r.done).toBe(false);
    expect(r.current && 'q' in r.current && r.current.fresh).toBe(true);
  });

  it('is done at the start where nothing is ready', () => {
    expect(run(0).done).toBe(true);
  });

  it('returns the attempt to store, and counts a new question introduced', () => {
    const r = run(1);
    const current = r.current as { q: Question };
    const rec = r.answer(result(current.q, true));
    expect(rec).toMatchObject({ course: 'c', id: current.q.id, ok: true });
    expect(r.introduced).toBe(1);
    expect(r.score).toBe(1);
  });

  it('reads its own answers before the copy holds them, and skips them once it does', () => {
    const r = run(1);
    const rec = r.answer(result((r.current as { q: Question }).q, true));
    expect(r.board(held())!.attempts((r.current as { q: Question }).q)).toHaveLength(1);
    expect(r.board(held([{ ...rec }]))!.attempts((r.current as { q: Question }).q)).toHaveLength(1);
  });

  it('ends when nothing is left, storing one stint', () => {
    // a miss days ago leaves `a` weak, and the review queue serves weak and due alone
    const old = [{ t: '2026-11-01T12:00:00+00:00', course: 'c', id: 'a', ok: false }];
    const r = new QueueRun(reviewQueue(Board.build(catalog, old), ['weak', 'due']), 'review', null, null, held(old));
    expect(r.current && 'q' in r.current && r.current.q.id).toBe('a');
    r.answer(result(q('a'), true));
    r.next(held(old));
    expect(r.done).toBe(true);
    expect(r.end()).toMatchObject({ mode: 'review', score: 1, n: 1 });
    expect(r.end()).toBeNull();
  });

  it('stores no stint where nothing was answered', () => {
    const r = run(1);
    r.stop();
    expect(r.done).toBe(true);
    expect(r.end()).toBeNull();
  });

  it('reopens a queue the limit ended on a raise, and returns the raise to store', () => {
    const r = run(0);
    expect(r.done).toBe(true);
    expect(r.reading(held(), Date.now()).raise).toBe(true);
    const shown = r.shown;
    expect(r.raise(held())).toMatchObject({ n: NEW_STEP });
    expect(r.done).toBe(false);
    expect(r.current && 'q' in r.current).toBe(true);
    expect(r.shown).toBeGreaterThan(shown);
    r.answer(result((r.current as { q: Question }).q, true));
    r.stop();
    expect(r.end()).toMatchObject({ n: 1 });
  });

  it('does not reopen a queue the user stopped', () => {
    const r = run(1);
    r.stop();
    r.raise(held());
    expect(r.done).toBe(true);
  });
});

describe('an exam run', () => {
  const plan = { mode: 'exam-L0', questions: [q('a'), q('b'), q('s')] };

  it('moves through every question, then stores its records together', () => {
    const r = new ExamRun(plan, catalog.courses);
    r.answer(result(q('a'), true));
    expect(r.next()).toBeNull();
    r.answer(result(q('b'), false));
    expect(r.next()).toBeNull();
    expect(r.last).toBe(true);
    r.answer(result(q('s'), true));
    const out = r.next();
    expect(r.phase).toBe('done');
    expect(out?.attempts).toHaveLength(3);
    expect(out?.session).toMatchObject({ mode: 'exam-L0', score: 2, n: 3 });
    expect(out?.cert).toBeNull();
    expect(r.end()).toBeNull();
  });

  it('stores nothing when stopped with nothing answered, and still reads its summary', () => {
    const r = new ExamRun(plan, catalog.courses);
    expect(r.stop()).toBeNull();
    expect(r.phase).toBe('done');
    expect(r.title).toBe('Done');
  });

  it('stores a certification exam stopped early as not passed', () => {
    const r = new ExamRun({ ...plan, mode: 'cert-x', cert: { course: 'c', id: 'x', passShare: 0.5 } }, catalog.courses);
    r.answer(result(q('a'), true));
    expect(r.stop()?.cert).toMatchObject({ course: 'c', cert: 'x', passed: false });
  });

  it('steps through the missed questions, then returns to the summary', () => {
    const r = new ExamRun(plan, catalog.courses);
    for (const [id, ok] of [
      ['a', false],
      ['b', true],
      ['s', false],
    ] as const) {
      r.answer(result(q(id), ok));
      r.next();
    }
    r.review();
    expect(r.phase).toBe('review');
    expect(r.reviewed?.q.id).toBe('a');
    expect(r.title).toBe('Missed 1 / 2');
    r.nextMissed();
    expect(r.reviewed?.q.id).toBe('s');
    expect(r.reviewLast).toBe(true);
    r.nextMissed();
    expect(r.phase).toBe('done');
  });
});
