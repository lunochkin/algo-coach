import { describe, expect, it } from 'vitest';

import {
  detailSections,
  loadSnapshot,
  parseQuestion,
  taughtBy,
  verdictView,
  youLine,
  yourAnswer,
  type Result,
} from './index';

const choice = parseQuestion(
  {
    id: 'x',
    topic: 't',
    sub: 's1',
    kind: 'concept',
    prompt: 'p',
    choices: ['a', 'b', 'c'],
    answer: ['A', 'C'],
    why: ['wa', 'wb', 'wc'],
    explain: 'because',
  },
  'c',
);
const short = parseQuestion(
  { id: 'y', topic: 't', sub: 's1', kind: 'output', prompt: 'p', format: 'short', accept: ['3', 'three'] },
  'c',
);
const open = parseQuestion(
  {
    id: 'z',
    topic: 't',
    sub: 's1',
    kind: 'concept',
    prompt: 'p',
    format: 'card',
    key: ['one', 'two'],
    key_detail: ['why one'],
    traps: ['t0', 't1'],
  },
  'c',
);
const result = (extra: Partial<Result>): Result => ({
  q: choice,
  correct: true,
  guess: false,
  order: [2, 0, 1],
  picked: [],
  reply: '',
  ...extra,
});

describe('the verdict', () => {
  it('names the key by displayed position where the reply was wrong', () => {
    // displayed A=c, B=a, C=b: the correct a and c sit at B and A
    expect(verdictView(result({ correct: false })).head).toEqual({ correct: false, text: '✗ Answer: AB.' });
  });

  it('says a correct guess is not yet passed', () => {
    expect(verdictView(result({ guess: true })).note).toMatch(/^Guessed/);
  });

  it('calls a wrong reply given without a guess a misconception', () => {
    expect(verdictView(result({ correct: false })).note).toMatch(/^Confidently wrong/);
  });

  it('gives an open question no verdict of its own, only the explanation', () => {
    expect(verdictView(result({ q: open })).head).toBeNull();
  });
});

describe("the learner's answer", () => {
  it('repeats the picks in displayed order, with the guess', () => {
    expect(youLine(result({ picked: [2, 0], guess: true }))).toBe('You: AC (guess)');
  });

  it("explains each option at its displayed position, marking the learner's", () => {
    const answer = yourAnswer(result({ picked: [1] }));
    expect(answer?.kind === 'rows' && answer.rows.map((r) => [r.mark, r.label, r.yours])).toEqual([
      ['✓', 'A) wc', false],
      ['✓', 'B) wa', true],
      ['✗', 'C) wb', false],
    ]);
  });

  it('shows a typed reply beside every accepted one', () => {
    expect(yourAnswer(result({ q: short, reply: '4' }))).toEqual({ kind: 'short', you: '4', accepted: '3, three' });
  });

  it("reads an open question's ticks: points missed, and the traps fallen into first", () => {
    const answer = yourAnswer(result({ q: open, card: { grade: 'p', missed: [1], traps: [1] } }));
    expect(answer?.kind === 'rows' && answer.rows.map((r) => [r.mark, r.label, r.note, r.yours])).toEqual([
      ['✓', '1. one', 'why one', false],
      ['✗', '2. two', '', false],
      ['✗', 'b) t1', '', true],
      ['·', 'a) t0', '', false],
    ]);
  });
});

describe('the detail', () => {
  it('reads only the sections the question carries, in reading order', () => {
    const q = { ...choice, detail: { mechanism: 'm', example: 'e', pitfalls: [], versions: '', diagram: 'd' } };
    expect(detailSections(q).map((x) => x.title)).toEqual(['Diagram', 'How it works', 'Example']);
  });

  it('has no section where the question carries no detail', () => {
    expect(detailSections(choice)).toEqual([]);
  });

  it('reads a diagram that is a markdown table as a table', () => {
    const diagram = '| method | 0 rows |\n|---|---|\n| `first()` | `None` |';
    const q = { ...choice, detail: { mechanism: 'm', example: '', pitfalls: [], versions: '', diagram } };
    expect(detailSections(q)[0]).toEqual({ title: 'Diagram', table: diagram });
  });

  it('reads a diagram that is one Mermaid fence as the seed\'s drawing', () => {
    const diagram = '```mermaid\nflowchart TB\n  a --> b\n```\n';
    const q = { ...choice, detail: { mechanism: 'm', example: '', pitfalls: [], versions: '', diagram } };
    expect(detailSections(q)[0]).toEqual({ title: 'Diagram', mermaid: 'flowchart TB\n  a --> b' });
  });

  it('keeps a drawing whose lines open with a bar as monospace', () => {
    const diagram = '│ a │ b │\n├───┼───┤\n│ 1 │ 2 │';
    const q = { ...choice, detail: { mechanism: 'm', example: '', pitfalls: [], versions: '', diagram } };
    expect(detailSections(q)[0]).toEqual({ title: 'Diagram', code: diagram, wrap: false });
  });
});

describe('the lessons a question links to', () => {
  const lesson = { title: 'Names', file: 'lessons/names.md', teaches: ['s1@1'], needs: [], pretest: 0 };
  const [c] = loadSnapshot({
    format: 6,
    courses: [
      {
        slug: 'c',
        definition: {
          title: 'C',
          pass_ratio: 1,
          kinds: ['concept'],
          topic: [{ slug: 't', tier: 1, title: 'T', subs: ['s1'] }],
        },
        questions: [],
        graph: { format: 2, lesson: { names: lesson } },
        lesson_bodies: { names: '# Names\n\n## Name binding\n' },
      },
    ],
  } as never).courses;

  it('links to its own lesson, at the section it names', () => {
    expect(taughtBy({ ...choice, lesson: 'names#name-binding' }, c)).toEqual([
      { course: 'c', slug: 'names', anchor: 'name-binding', label: '📖 Learn this: Names › Name binding', read: false },
    ]);
  });

  it('says which of its lessons are read', () => {
    const done = new Set(['c:names']);
    expect(taughtBy({ ...choice, lesson: 'names' }, c, done)[0]).toMatchObject({
      label: '📖 Learn this: Names · read',
      read: true,
    });
    expect(taughtBy(choice, c, done).map((x) => x.label)).toEqual(['From lesson: Names · read']);
  });

  it('otherwise names the lessons teaching its subtopic at its level', () => {
    expect(taughtBy(choice, c).map((x) => x.label)).toEqual(['From lesson: Names']);
  });
});
