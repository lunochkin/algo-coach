import { describe, expect, it } from 'vitest';

import {
  askAct,
  askReducer,
  askResult,
  claimDeclined,
  initialAsk,
  parseQuestion,
  sendClaim,
  type AskState,
  type EngineClient,
} from './index';

const choice = parseQuestion(
  { id: 'x', topic: 't', sub: 's', kind: 'concept', prompt: 'p', choices: ['a', 'b'], answer: ['A'], explain: 'e' },
  'c',
);
const open = parseQuestion(
  { id: 'z', topic: 't', sub: 's', kind: 'concept', prompt: 'p', format: 'card', key: ['one', 'two'], traps: [] },
  'c',
);
const step = (s: AskState, ...events: Parameters<typeof askReducer>[1][]) => events.reduce(askReducer, s);

describe("a question's press", () => {
  it('asks for an answer, enabled once something is picked', () => {
    expect(askAct(choice, initialAsk(), null)).toEqual({ act: 'submit', label: 'Submit', enabled: false });
    const picked = step(initialAsk(), { type: 'pick', pos: 0, multi: false });
    expect(askAct(choice, picked, null).enabled).toBe(true);
  });

  it('reveals an open question, then grades it', () => {
    expect(askAct(open, initialAsk(), null).act).toBe('reveal');
    const revealed = step(initialAsk(), { type: 'reveal' }, { type: 'recall', i: 0 });
    expect(askAct(open, revealed, null).act).toBe('grade');
  });

  it('moves on once answered, and finishes an exam on its last question', () => {
    const answered = step(initialAsk(), { type: 'pick', pos: 0, multi: false });
    const done = askReducer(answered, { type: 'answered', result: askResult(choice, [0, 1], answered) });
    expect(askAct(choice, done, null)).toEqual({ act: 'next', label: 'Next', enabled: true });
    expect(askAct(choice, done, { last: true }).label).toBe('Finish');
  });

  it('takes no pick once answered', () => {
    const answered = step(initialAsk(), { type: 'pick', pos: 0, multi: false });
    const done = askReducer(answered, { type: 'answered', result: askResult(choice, [0, 1], answered) });
    expect(askReducer(done, { type: 'pick', pos: 1, multi: false }).picked).toEqual([0]);
  });
});

describe("the claim's send", () => {
  it('clears the ticks on a decline, and keeps them empty on undoing it', () => {
    expect(claimDeclined(false, ['dp'])).toEqual({ declined: true, chosen: [] });
    expect(claimDeclined(true, [])).toEqual({ declined: false, chosen: [] });
  });

  it('sends the label only where a mode was picked', async () => {
    const calls: string[] = [];
    const client = {
      POST: (path: string) => {
        calls.push(path);
        return Promise.resolve({ data: {} });
      },
    } as unknown as EngineClient;
    const form = { chosen: ['dp'], declined: false, confidence: 'sure' as const, mode: null };
    expect(await sendClaim(client, 'a1', form)).toBeNull();
    expect(calls).toEqual(['/api/attempts/{attempt_id}/claims']);
    await sendClaim(client, 'a1', { ...form, mode: 'gap' });
    expect(calls.slice(1)).toEqual(['/api/attempts/{attempt_id}/claims', '/api/attempts/{attempt_id}/labels']);
  });
});
