import { describe, expect, it } from 'vitest';

import {
  boardView,
  cardBlocks,
  cardRow,
  inProgress,
  ladderView,
  notInProgress,
  problemCards,
  problemTried,
  readFailure,
  recallLine,
  revealLabel,
  techniqueCards,
  techniqueStats,
  type components,
} from './index';

type ListedCard = components['schemas']['ListedCard'];
type Template = components['schemas']['Template'];

const NOW = Date.parse('2026-11-10T12:00:00Z');

const template = (id: string, extra: Partial<Template> = {}): Template =>
  ({
    id,
    slug: id,
    title: id,
    trigger: '',
    optional: false,
    speedup: false,
    kind: 'code',
    code: '',
    unordered: false,
    cases: [{}],
    ...extra,
  }) as Template;

const card = (slug: string, extra: Partial<ListedCard> = {}, status: Partial<ListedCard['status']> = {}): ListedCard =>
  ({
    id: slug,
    slug,
    technique: slug,
    title: slug,
    trigger: 'When **sorted**',
    brief: '',
    family: slug,
    templates: [template(`${slug}-a`)],
    selector: {},
    ...extra,
    status: {
      started_at: null,
      state: 'not_started',
      rungs: 0,
      solved: 0,
      required: 0,
      required_solved: 0,
      gaps: 0,
      recall: [],
      last_at: null,
      ...status,
    },
  }) as ListedCard;

describe("a technique's row", () => {
  it('reads an untouched technique as never', () => {
    expect(techniqueStats({ attempt_count: 0, solved_count: 0 }, NOW)).toEqual([
      { label: 'attempted', value: 'never' },
    ]);
  });

  it('counts attempts, the solved share and the last attempt', () => {
    expect(techniqueStats({ attempt_count: 1, solved_count: 1, last_attempt_at: '2026-11-09T12:00:00Z' }, NOW)).toEqual(
      [
        { label: 'attempt', value: 1 },
        { label: 'solved', value: '1/1' },
        { label: '', value: 'yesterday' },
      ],
    );
  });
});

describe('the board', () => {
  const row = (technique: string, attempt_count: number) => ({
    technique,
    attempt_count,
    solved_count: 0,
    self_labels: {},
  });

  it('splits the techniques never practised from the rest', () => {
    const view = boardView({ rows: [row('a', 0), row('b', 2)], ungrouped: 0, excluded: 0 });
    expect(view.untouched.map((one) => one.technique)).toEqual(['a']);
    expect(view.practised.map((one) => one.technique)).toEqual(['b']);
    expect(view.foot).toBeNull();
  });

  it('names the attempts no row holds in one line', () => {
    expect(boardView({ rows: [], ungrouped: 1, excluded: 3 }).foot).toBe(
      '1 attempt grouped nowhere · 3 on a defective problem',
    );
  });
});

describe("a problem's facts", () => {
  it('reads an untouched problem as never attempted', () => {
    expect(problemTried({ attempt_count: 0, solved_count: 0, last_attempt_at: null }, NOW)).toBe('never attempted');
  });

  it('counts the attempts, the solved share and the last attempt', () => {
    expect(problemTried({ attempt_count: 1, solved_count: 1, last_attempt_at: '2026-11-09T12:00:00Z' }, NOW)).toBe(
      '1 attempt, 1/1 solved, last yesterday',
    );
  });

  it("offers the cards of the pick's technique, a narrower card counting for its family", () => {
    const cards = [card('dp', { family: 'dp' }), card('knapsack', { family: 'dp' }), card('bfs')];
    expect(problemCards(cards, ['dp', 'bfs'], 'dp').map((one) => one.slug)).toEqual(['dp', 'knapsack']);
    expect(problemCards(cards, ['dp', 'bfs'], null).map((one) => one.slug)).toEqual(['dp', 'knapsack', 'bfs']);
  });
});

describe('the cards in progress', () => {
  const at = '2026-11-01T00:00:00Z';

  it('lists the acquiring and consolidating cards, the most recently active first', () => {
    const cards = [
      card('a', {}, { started_at: at, state: 'acquiring', last_at: '2026-11-02T00:00:00Z' }),
      card('b'),
      card('c', {}, { started_at: at, state: 'consolidating', last_at: '2026-11-05T00:00:00Z' }),
    ];
    expect(inProgress(cards).map((one) => one.slug)).toEqual(['c', 'a']);
  });

  it('counts a graduated and a lapsed card out, and lists them with the rest', () => {
    const cards = [
      card('done', {}, { started_at: at, state: 'graduated' }),
      card('lost', {}, { started_at: at, state: 'lapsed' }),
      card('new'),
    ];
    expect(inProgress(cards)).toEqual([]);
    expect(notInProgress(cards).map((one) => one.slug)).toEqual(['done', 'lost', 'new']);
  });
});

describe("a technique's cards", () => {
  it("reads the cards the engine names, in the cards list's order", () => {
    const listed = [card('a'), card('b'), card('c')];
    expect(techniqueCards(listed, [{ slug: 'c' }, { slug: 'a' }]).map((one) => one.slug)).toEqual(['a', 'c']);
  });
});

describe("the cards list's blocks", () => {
  it('heads a family several cards teach, and leaves a family of one unheaded', () => {
    const cards = [card('dp', { family: 'dp' }), card('knapsack', { family: 'dp' }), card('bfs'), card('dfs')];
    expect(cardBlocks(cards).map((one) => [one.technique, one.cards.map((c) => c.slug)])).toEqual([
      ['dp', ['dp', 'knapsack']],
      [null, ['bfs', 'dfs']],
    ]);
  });
});

describe("a card's row", () => {
  it('reads an unstarted card by its trigger and its templates', () => {
    const row = cardRow(card('a', { templates: [template('x'), template('y', { optional: true })] }), null, NOW);
    expect(row).toMatchObject({
      technique: 'a',
      aside: '2 templates, 1 optional',
      trigger: 'When sorted',
      state: null,
      progress: null,
    });
  });

  it('leaves the technique off a row its heading names', () => {
    expect(cardRow(card('a'), 'a', NOW).technique).toBeNull();
  });

  it('reads a started card by its ladder and the forms it leaves uncovered', () => {
    const started = card(
      'a',
      {},
      {
        started_at: '2026-11-01T00:00:00Z',
        last_at: '2026-11-10T08:00:00Z',
        rungs: 4,
        solved: 2,
        required: 3,
        required_solved: 1,
        gaps: 1,
      },
    );
    const row = cardRow(started, null, NOW);
    expect(row.aside).toBe('today');
    expect(row.trigger).toBeNull();
    expect(row.state).toMatch(/^started .+ · ladder 2\/4, required 1\/3 · 1 form uncovered$/);
    expect(row.progress).toEqual({ solved: 2, rungs: 4 });
  });

  it('marks each template by its last recall', () => {
    const recalled = card(
      'a',
      {
        templates: [
          template('read', { cases: [] }),
          template('never'),
          template('failed'),
          template('hinted'),
          template('clean'),
        ],
      },
      {
        recall: [
          { template_id: 'failed', last_at: '2026-11-01T00:00:00Z', hints: [], verified: false },
          { template_id: 'hinted', last_at: '2026-11-01T00:00:00Z', hints: ['notes'], verified: true },
          { template_id: 'clean', last_at: '2026-11-01T00:00:00Z', hints: [], verified: true },
        ],
      },
    );
    expect(cardRow(recalled, null, NOW).recall.map((one) => [one.mark, one.tone])).toEqual([
      ['-', null],
      ['·', null],
      ['✗', 'wrong'],
      ['◐', null],
      ['✓', 'passed'],
    ]);
  });
});

describe("a card's templates", () => {
  it('reads a recall with its hints', () => {
    expect(recallLine(undefined, NOW)).toBe('Never recalled');
    expect(
      recallLine({ template_id: 'x', last_at: '2026-11-10T08:00:00Z', hints: ['notes'], verified: true }, NOW),
    ).toBe('Recalled today · passed · 1 hint');
  });

  it('covers a form with its length alone', () => {
    expect(revealLabel('def solve():\n    return 1\n')).toBe('Reveal the form · 2 lines');
  });
});

describe('a failed read', () => {
  it('says the device holds no copy when the network is down', () => {
    expect(readFailure('the cards', 'TypeError: Network request failed')).toBe(
      'No connection, and this device holds no copy of the cards.',
    );
    expect(readFailure('the card', '/cards/x 404: gone')).toBe('The card did not load: /cards/x 404: gone');
  });
});

describe("a card's ladder", () => {
  const rung = (id: string, templates: string[], required: boolean, solved = false) => ({
    problem: { id, title: id, difficulty: 'easy' },
    templates,
    required,
    solved,
  });
  const studied = (run: boolean) =>
    ({
      card: { templates: [template('t1', { title: 'Lower bound' })] },
      run: run ? { started_at: '2026-11-01T00:00:00Z' } : null,
      rungs: [rung('p1', ['t1'], true, true), rung('p2', [], false)],
      gaps: [{ template_id: 't2', slug: 't2', title: 'Upper bound' }],
      recall: [],
      probes: [],
    }) as unknown as components['schemas']['Studied'];

  it('counts the rungs before a run, and the solved ones once it is open', () => {
    expect(ladderView(studied(false)).aside).toBe('2 rungs');
    expect(ladderView(studied(true)).aside).toBe('1 of 2 solved');
  });

  it('names what a rung covers and whether it is required, and the gaps', () => {
    const view = ladderView(studied(true));
    expect(view.rows.map((one) => [one.covers, one.need, one.solved])).toEqual([
      ['covers Lower bound', 'required', true],
      [null, 'optional', false],
    ]);
    expect(view.gaps).toEqual(['No problem covers Upper bound yet.']);
    expect(ladderView(studied(false)).rows[0].solved).toBeNull();
  });
});
