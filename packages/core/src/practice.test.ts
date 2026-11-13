import { describe, expect, it } from 'vitest';

import {
  boardView,
  cardEdges,
  cardNeeds,
  cardRow,
  briefParts,
  cardSections,
  inProgress,
  cardNote,
  cardProgress,
  runLock,
  runStartLabel,
  ladderView,
  depthSections,
  problemCards,
  problemFacts,
  problemTried,
  readFailure,
  recallLine,
  revealLabel,
  startCardRun,
  techniqueCards,
  techniqueStats,
  templateView,
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
    depth: 0,
    met: false,
    waiting: [],
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

  it('names a missing difficulty, and offers no cards label where no card is offered', () => {
    const facts = problemFacts(
      { difficulty: null, techniques: ['bfs'], attempt_count: 0, solved_count: 0, last_attempt_at: null },
      [card('dp')],
      null,
      NOW,
    );
    expect(facts).toMatchObject({ difficulty: 'no difficulty', techniques: 'bfs', cards: [], cardsLabel: null });
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
  });
});

describe("a technique's cards", () => {
  it("reads the cards the engine names, in the cards list's order", () => {
    const listed = [card('a'), card('b'), card('c')];
    expect(techniqueCards(listed, [{ slug: 'c' }, { slug: 'a' }]).map((one) => one.slug)).toEqual(['a', 'c']);
  });
});

describe('the card graph', () => {
  const needs = (slug: string, ...required: string[]) =>
    card(slug, { requires: required.map((one) => ({ card: one, template: 'x', used_by: 'y' })) });

  it('heads each depth, the roots first', () => {
    const cards = [card('b', { depth: 1 }), card('a'), card('c', { depth: 2 }), card('d', { depth: 1 })];
    expect(depthSections(cards).map((one) => [one.title, one.cards.map((c) => c.slug)])).toEqual([
      ['Depth 0, roots', ['a']],
      ['Depth 1', ['b', 'd']],
      ['Depth 2', ['c']],
    ]);
  });

  it('draws one edge per required card, and none to a card not listed', () => {
    const cards = [card('a'), needs('b', 'a', 'a'), needs('c', 'b', 'gone')];
    expect(cardEdges(cards)).toEqual([
      { from: 'a', to: 'b' },
      { from: 'b', to: 'c' },
    ]);
  });

  it("names a card's required cards with a tick on each met, and nothing on a root", () => {
    const cards = [card('a', { met: true }), card('b'), needs('c', 'a', 'b')];
    expect(cardNeeds(cards[2], cards)).toBe('needs a ✓, b');
    expect(cardNeeds(cards[0], cards)).toBeNull();
  });
});

describe("a card's row", () => {
  it('reads an unstarted card by its trigger', () => {
    const row = cardRow(card('a'), null, NOW);
    expect(row).toMatchObject({
      technique: 'a',
      aside: 'not started',
      waits: null,
      trigger: 'When sorted',
      state: null,
      progress: null,
    });
  });

  it('reads a locked card by what it waits on, in place of its trigger', () => {
    const row = cardRow(card('a', { waiting: [{ slug: 'h', title: 'Hashing' }] }), null, NOW);
    expect([row.aside, row.waits, row.trigger]).toEqual(['locked', 'waits on Hashing', null]);
  });

  it('reads a met card as met', () => {
    expect(cardRow(card('a', { met: true }), null, NOW).aside).toBe('met');
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

  it('says a form no case checks is read and never recalled, where the recall press would sit', () => {
    const view = templateView({ cases: [], optional: true, kind: 'procedure', code: 'x\n' }, undefined, NOW);
    expect(view).toMatchObject({
      recallable: false,
      badges: ['optional', 'procedure'],
      status: 'No case checks this form',
    });
    expect(view.unchecked).not.toBeNull();
    const checked = templateView({ cases: [{}] as never, optional: false, kind: 'code', code: 'x\n' }, undefined, NOW);
    expect([checked.recallable, checked.unchecked, checked.status]).toEqual([true, null, 'Never recalled']);
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
      waiting: [],
    }) as unknown as components['schemas']['Studied'];

  it('counts the rungs before a run, and the solved ones once it is open', () => {
    expect(ladderView(studied(false)).count).toBe(2);
    expect(ladderView(studied(false)).aside).toBeNull();
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

  it("reads a run's progress: the rungs solved, and the rung next", () => {
    const progress = cardProgress(studied(true));
    expect([progress.solved, progress.rungs, progress.next?.problemId]).toEqual([1, 2, 'p2']);
    // the fixture's template carries its cases, so a recall is offered
    expect(progress.recallable).toBe(true);
  });

  it('names the technique under the title, and since when a run studies it', () => {
    const one = { ...studied(true), card: { ...studied(true).card, technique: 'binary-search' } };
    expect(cardNote(one, Date.parse('2026-11-01T00:00:00Z'))).toMatch(/^binary-search · studying since /);
    expect(cardNote({ ...one, run: null }, 0)).toBe('binary-search');
  });
});

describe("a card's sections and its run", () => {
  it('names the probes only once a run drew some', () => {
    const card = { brief: 'Read this first.\n\n## Core idea\n\nA boundary.\n\n## Ladder\n\nNot the ladder.' };
    expect(cardSections({ probes: [], card }).map((one) => one.id)).toEqual([
      'trigger',
      'brief',
      'brief-core-idea',
      'brief-ladder',
      'ladder',
      'templates',
    ]);
    expect(cardSections({ probes: [{}] as never, card }).map((one) => one.id)).toContain('probes');
    expect(cardSections(null)).toEqual([]);
  });

  it('reads a brief opening on a heading as its headings alone', () => {
    expect(briefParts('## Core idea\n\nA boundary.').map((one) => one.title)).toEqual(['Core idea']);
  });

  it('names a refused start rather than reading it as started', async () => {
    const refusing = { POST: () => Promise.resolve({ error: { detail: 'no' } }) } as unknown as Parameters<
      typeof startCardRun
    >[0];
    expect((await startCardRun(refusing, 'dp')).ok).toBe(false);
    const starting = { POST: () => Promise.resolve({ data: {} }) } as unknown as Parameters<typeof startCardRun>[0];
    expect(await startCardRun(starting, 'dp')).toEqual({ ok: true, value: null });
  });
});

describe("a locked card's press", () => {
  const waiting = (...titles: string[]) => titles.map((title) => ({ slug: title, title }));

  it('reads no lock where nothing is waited on', () => {
    expect(runLock([])).toBeNull();
    expect(runStartLabel(false)).toBe('Start studying this card');
  });

  it('names every card waited on, and how one is met', () => {
    expect(runLock(waiting('Hashing'))).toBe(
      'Waits on Hashing. A card is met by solving its ladder, or one of its probes.',
    );
    expect(runLock(waiting('Hashing', 'Two pointers', 'Prefix sum'))).toMatch(
      /^Waits on Hashing, Two pointers and Prefix sum\./,
    );
    expect(runStartLabel(false, true)).toBe('Locked');
  });
});
