import { describe, expect, it } from 'vitest';

import {
  beginSitting,
  clockState,
  moveSitting,
  sittingControls,
  submitToSitting,
  touchSitting,
  type components,
  type EngineClient,
} from './index';

type Sitting = components['schemas']['Sitting'];

const sitting = (over: Partial<Sitting> = {}): Sitting =>
  ({ id: 's1', clock_started_at: null, ended_at: null, pauses: [], ...over }) as Sitting;

// a client answering each path it is asked by, and keeping the calls in order
function fake(answers: Record<string, unknown>) {
  const calls: string[] = [];
  const answer = (path: string) => {
    calls.push(path);
    const data = answers[path];
    return Promise.resolve(data === undefined ? { error: { detail: `no ${path}` } } : { data });
  };
  const client = { POST: answer, GET: answer } as unknown as EngineClient;
  return { client, calls };
}

const now = () => 7;

describe("the sitting's controls", () => {
  it('offers one clock press by state, and End only on a sitting that exists', () => {
    expect(sittingControls(clockState(null), null)).toEqual({
      clock: { to: 'start', label: 'Start' },
      end: false,
      touch: false,
    });
    const running = sitting({ clock_started_at: '2026-11-11T10:00:00Z' });
    expect(sittingControls(clockState(running), 's1').clock).toEqual({ to: 'pause', label: 'Pause' });
    const paused = sitting({
      clock_started_at: '2026-11-11T10:00:00Z',
      pauses: [{ at: '2026-11-11T10:05:00Z', until: null }],
    } as Partial<Sitting>);
    expect(sittingControls(clockState(paused), 's1').clock).toEqual({ to: 'resume', label: 'Start' });
  });

  it('offers nothing on an ended sitting, and stops touching it', () => {
    const ended = sitting({ ended_at: '2026-11-11T11:00:00Z' });
    expect(sittingControls(clockState(ended), 's1')).toEqual({ clock: null, end: false, touch: false });
  });
});

describe("the sitting's requests", () => {
  it('mints the sitting before a start that finds none', async () => {
    const { client, calls } = fake({
      '/api/problems/{problem_id}/sittings': { sitting: sitting({ id: 'new' }), elapsed_sec: null },
      '/api/sittings/{sitting_id}/start': { sitting: sitting({ id: 'new' }), elapsed_sec: 0 },
    });
    const moved = await moveSitting(client, 'p1', 'web', null, 'start', now);
    expect(calls).toEqual(['/api/problems/{problem_id}/sittings', '/api/sittings/{sitting_id}/start']);
    expect(moved.ok && moved.value).toMatchObject({ elapsedSec: 0, at: 7 });
    expect(moved.minted?.sitting.id).toBe('new');
  });

  it('refuses a pause where no sitting runs, asking nothing of the engine', async () => {
    const { client, calls } = fake({});
    const moved = await moveSitting(client, 'p1', 'web', null, 'pause', now);
    expect(moved.ok).toBe(false);
    expect(calls).toEqual([]);
  });

  it('names the minted sitting even where the move after it is refused', async () => {
    const { client } = fake({
      '/api/problems/{problem_id}/sittings': { sitting: sitting({ id: 'new' }), elapsed_sec: null },
    });
    const moved = await moveSitting(client, 'p1', 'web', null, 'start', now);
    expect(moved.ok).toBe(false);
    expect(moved.minted?.sitting.id).toBe('new');
  });

  it("reads a submission's elapsed time from the attempt it minted", async () => {
    const { client } = fake({
      '/api/sittings/{sitting_id}/submissions': {
        sitting: sitting({ ended_at: '2026-11-11T11:00:00Z' }),
        attempt: { time_to_solve_sec: 42 },
      },
    });
    const sent = await submitToSitting(client, 'p1', 'web', 's1', { code: 'x', restored: false }, now);
    expect(sent.ok && sent.value.moved.elapsedSec).toBe(42);
  });

  it('reports a refusal in words rather than throwing', async () => {
    const { client } = fake({});
    const begun = await beginSitting(client, 'p1', 'web', now);
    expect(begun).toEqual({ ok: false, refused: expect.any(String) });
    const touched = await touchSitting(client, 's1', now);
    expect(touched.ok).toBe(false);
  });
});
