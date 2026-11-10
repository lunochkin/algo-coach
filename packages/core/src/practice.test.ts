import { describe, expect, it } from 'vitest';

import { boardView, cardBlocks, cardRow, inProgress, readFailure, recallLine, revealLabel, techniqueStats, type components } from './index';

type ListedCard = components['schemas']['ListedCard'];
type Template = components['schemas']['Template'];

const NOW = Date.parse('2026-11-10T12:00:00Z');

const template = (id: string, extra: Partial<Template> = {}): Template =>
  ({ id, slug: id, title: id, trigger: '', optional: false, speedup: false, kind: 'code', code: '', unordered: false, cases: [{}], ...extra }) as Template;

const card = (slug: string, extra: Partial<ListedCard> = {}, status: Partial<ListedCard['status']> = {}): ListedCard =>
  ({
    id: slug, slug, technique: slug, title: slug, trigger: 'When **sorted**', brief: '', family: slug,
    templates: [template(`${slug}-a`)], selector: {},
    ...extra,
    status: { started_at: null, rungs: 0, solved: 0, required: 0, required_solved: 0, gaps: 0, recall: [], last_at: null, ...status },
  }) as ListedCard;

describe("a technique's row", () => {
  it('reads an untouched technique as never', () => {
    expect(techniqueStats({ attempt_count: 0, solved_count: 0 }, NOW)).toEqual([{ label: 'attempted', value: 'never' }]);
  });

  it('counts attempts, the solved share and the last attempt', () => {
    expect(techniqueStats({ attempt_count: 1, solved_count: 1, last_attempt_at: '2026-11-09T12:00:00Z' }, NOW)).toEqual([
      { label: 'attempt', value: 1 },
      { label: 'solved', value: '1/1' },
      { label: '', value: 'yesterday' },
    ]);
  });
});

describe('the board', () => {
  const row = (technique: string, attempt_count: number) => ({ technique, attempt_count, solved_count: 0, self_labels: {} });

  it('splits the techniques never practised from the rest', () => {
    const view = boardView({ rows: [row('a', 0), row('b', 2)], ungrouped: 0, excluded: 0 });
    expect(view.untouched.map((one) => one.technique)).toEqual(['a']);
    expect(view.practised.map((one) => one.technique)).toEqual(['b']);
    expect(view.foot).toBeNull();
  });

  it('names the attempts no row holds in one line', () => {
    expect(boardView({ rows: [], ungrouped: 1, excluded: 3 }).foot).toBe('1 attempt grouped nowhere · 3 on a defective problem');
  });
});

describe('the cards in progress', () => {
  it('lists the started cards, the most recently active first', () => {
    const cards = [
      card('a', {}, { started_at: '2026-11-01T00:00:00Z', last_at: '2026-11-02T00:00:00Z' }),
      card('b'),
      card('c', {}, { started_at: '2026-11-01T00:00:00Z', last_at: '2026-11-05T00:00:00Z' }),
    ];
    expect(inProgress(cards).map((one) => one.slug)).toEqual(['c', 'a']);
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
    expect(row).toMatchObject({ technique: 'a', aside: '2 templates, 1 optional', trigger: 'When sorted', state: null, progress: null });
  });

  it('leaves the technique off a row its heading names', () => {
    expect(cardRow(card('a'), 'a', NOW).technique).toBeNull();
  });

  it('reads a started card by its ladder and the forms it leaves uncovered', () => {
    const started = card('a', {}, { started_at: '2026-11-01T00:00:00Z', last_at: '2026-11-10T08:00:00Z', rungs: 4, solved: 2, required: 3, required_solved: 1, gaps: 1 });
    const row = cardRow(started, null, NOW);
    expect(row.aside).toBe('today');
    expect(row.trigger).toBeNull();
    expect(row.state).toMatch(/^started .+ · ladder 2\/4, required 1\/3 · 1 form uncovered$/);
    expect(row.progress).toEqual({ solved: 2, rungs: 4 });
  });

  it('marks each template by its last recall', () => {
    const recalled = card(
      'a',
      { templates: [template('read', { cases: [] }), template('never'), template('failed'), template('hinted'), template('clean')] },
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
    expect(recallLine({ template_id: 'x', last_at: '2026-11-10T08:00:00Z', hints: ['notes'], verified: true }, NOW)).toBe(
      'Recalled today · passed · 1 hint',
    );
  });

  it('covers a form with its length alone', () => {
    expect(revealLabel('def solve():\n    return 1\n')).toBe('Reveal the form · 2 lines');
  });
});

describe('a failed read', () => {
  it('says the device holds no copy when the network is down', () => {
    expect(readFailure('the cards', 'TypeError: Network request failed')).toBe(
      'No connection. The cards are read from the engine, and this device holds no copy.',
    );
    expect(readFailure('the card', '/cards/x 404: gone')).toBe('The card did not load: /cards/x 404: gone');
  });
});
