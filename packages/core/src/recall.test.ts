import { describe, expect, it } from 'vitest';

import {
  failures,
  nextHint,
  recallBlank,
  recallMenu,
  recallView,
  runRecall,
  type components,
  type EngineClient,
} from './index';

type RecallAttempt = components['schemas']['RecallAttempt'];
type Outcome = components['schemas']['CaseOutcome'];

const ran = (outcomes: Outcome[], hints: RecallAttempt['hints'] = []): RecallAttempt =>
  ({ results: outcomes.map((outcome, i) => ({ case_id: `c${i}`, outcome })), hints }) as RecallAttempt;

describe('the recall trainer', () => {
  it('offers the notes, then the form, then nothing', () => {
    expect([nextHint([]), nextHint(['notes']), nextHint(['notes', 'form'])]).toEqual(['notes', 'form', null]);
  });

  it('opens on the signature and an indented blank line', () => {
    expect(recallBlank('def solve(a, x):')).toBe('def solve(a, x):\n    ');
  });

  it('reads a clean pass as recalled cold', () => {
    const view = recallView(ran(['passed', 'passed']));
    expect(view).toEqual({
      recalled: true,
      verdict: 'Recalled: 2 of 2 cases passed',
      failures: null,
      hints: 'Recalled cold, with no hint taken.',
    });
  });

  it('names the failures by severity, and the hints a pass took', () => {
    const view = recallView(ran(['wrong', 'crashed', 'passed', 'wrong'], ['notes']));
    expect(view.recalled).toBe(false);
    expect(view.failures).toBe('1 crashed · 2 wrong answer');
    expect(view.hints).toBe('Taken on the way: the notes.');
  });

  it('reads a run with no cases as not recalled', () => {
    expect(recallView(ran([])).recalled).toBe(false);
    expect(failures([])).toEqual([]);
  });
});

describe("the trainer's menu and requests", () => {
  const templates = [
    { slug: 'a', title: 'Lower bound', optional: false, recallable: true },
    { slug: 'b', title: 'Upper bound', optional: true, recallable: true },
    { slug: 'c', title: 'Procedure', optional: false, recallable: false },
  ] as components['schemas']['Prompted']['templates'];

  it('names each form, offers none no case checks, and names the one recalled', () => {
    const menu = recallMenu({ templates, template_slug: 'b' });
    expect(menu.here).toBe('Upper bound');
    expect(menu.items.map((one) => [one.note, one.enabled, one.current])).toEqual([
      [null, true, false],
      ['optional', true, true],
      ['no cases', false, false],
    ]);
    expect(recallMenu({ templates, template_slug: 'zz' }).here).toBe('a form');
  });

  it('reports a refused run in words rather than throwing', async () => {
    const client = { POST: () => Promise.resolve({ error: { detail: 'too many' } }) } as unknown as EngineClient;
    const ran = await runRecall(client, 'card', 'a', 'code', []);
    expect(ran.ok).toBe(false);
  });
});
