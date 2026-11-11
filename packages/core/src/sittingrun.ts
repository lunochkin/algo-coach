import type { components } from './api/schema';
import { described, type EngineClient } from './engine';
import { CLOCK_PAUSE, CLOCK_START, type ClockMove, type ClockState } from './sitting';

// a sitting's controller, for every platform: the requests that mint it, move
// its clock, submit to it and read it back, and what the clock's presses
// offer. Each platform holds the result in its own state and times its own
// touches: `flows.md`, Drill loop

type Sitting = components['schemas']['Sitting'];
type Submitted = components['schemas']['Submitted'];

/** The sitting as the engine last read it, with when the platform received that reading. */
export interface Moved {
  sitting: Sitting;
  elapsedSec: number | null;
  at: number;
}

export type Outcome<T> = { ok: true; value: T } | { ok: false; refused: string };

// a reading touches the sitting, well under the 45 minutes an untouched
// sitting is ended at: `log.md`, Sittings
export const TOUCH_MS = 10 * 60 * 1000;

/** What the sitting's bar offers: the clock's one press, End, and whether the platform keeps touching it. */
export interface SittingControls {
  clock: { to: 'start' | 'resume' | 'pause'; label: string } | null;
  end: boolean;
  touch: boolean;
}

/**
 * One press for the clock: it starts a clock that never ran, resumes a paused
 * one and pauses a running one. End needs a sitting to end, and an ended
 * sitting offers neither and is touched no more.
 */
export function sittingControls(state: ClockState, sittingId: string | null): SittingControls {
  if (state.ended) return { clock: null, end: false, touch: false };
  const clock = state.unstarted
    ? { to: 'start' as const, label: CLOCK_START }
    : state.paused
      ? { to: 'resume' as const, label: CLOCK_START }
      : { to: 'pause' as const, label: CLOCK_PAUSE };
  return { clock, end: sittingId !== null, touch: sittingId !== null };
}

const reading = (sitting: Sitting, elapsedSec: number | null, now: number): Moved => ({ sitting, elapsedSec, at: now });

async function attempt<T>(run: () => Promise<Outcome<T>>): Promise<Outcome<T>> {
  try {
    return await run();
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}

/** The first clock press or submission mints the sitting it runs in, named by its device. */
export function beginSitting(
  client: EngineClient,
  problemId: string,
  device: string,
  now: () => number,
): Promise<Outcome<Moved>> {
  return attempt(async () => {
    const { data, error } = await client.POST('/api/problems/{problem_id}/sittings', {
      params: { path: { problem_id: problemId } },
      body: { device },
    });
    return data
      ? { ok: true, value: reading(data.sitting, data.elapsed_sec, now()) }
      : { ok: false, refused: described(error) };
  });
}

/**
 * Moves the clock, minting the sitting first where a start finds none. The
 * minted sitting is returned beside the move, so a refused start still names it.
 */
export function moveSitting(
  client: EngineClient,
  problemId: string,
  device: string,
  sittingId: string | null,
  to: ClockMove,
  now: () => number,
): Promise<Outcome<Moved> & { minted?: Moved }> {
  return attempt(async () => {
    let id = sittingId;
    let minted: Moved | undefined;
    if (id === null) {
      if (to !== 'start') return { ok: false, refused: 'no sitting to move' };
      const begun = await beginSitting(client, problemId, device, now);
      if (!begun.ok) return begun;
      minted = begun.value;
      id = begun.value.sitting.id;
    }
    const params = { params: { path: { sitting_id: id } } };
    const { data, error } =
      to === 'start'
        ? await client.POST('/api/sittings/{sitting_id}/start', params)
        : to === 'pause'
          ? await client.POST('/api/sittings/{sitting_id}/pause', params)
          : to === 'resume'
            ? await client.POST('/api/sittings/{sitting_id}/resume', params)
            : await client.POST('/api/sittings/{sitting_id}/end', params);
    if (data) return { ok: true, value: reading(data.sitting, data.elapsed_sec, now()), minted };
    return { ok: false, refused: described(error), minted };
  });
}

/** A submission, minting the sitting where none runs. A solve ends the sitting, which the reading carries. */
export function submitToSitting(
  client: EngineClient,
  problemId: string,
  device: string,
  sittingId: string | null,
  body: { code: string; restored: boolean },
  now: () => number,
): Promise<Outcome<{ submitted: Submitted; moved: Moved }> & { minted?: Moved }> {
  return attempt(async () => {
    let id = sittingId;
    let minted: Moved | undefined;
    if (id === null) {
      const begun = await beginSitting(client, problemId, device, now);
      if (!begun.ok) return begun;
      minted = begun.value;
      id = begun.value.sitting.id;
    }
    const { data, error } = await client.POST('/api/sittings/{sitting_id}/submissions', {
      params: { path: { sitting_id: id } },
      body,
    });
    if (!data) return { ok: false, refused: described(error), minted };
    return {
      ok: true,
      value: { submitted: data, moved: reading(data.sitting, data.attempt.time_to_solve_sec ?? null, now()) },
      minted,
    };
  });
}

/** Reads the sitting back, which touches it, so a solver thinking keeps it running. */
export function touchSitting(client: EngineClient, sittingId: string, now: () => number): Promise<Outcome<Moved>> {
  return attempt(async () => {
    const { data, error } = await client.GET('/api/sittings/{sitting_id}', {
      params: { path: { sitting_id: sittingId } },
    });
    return data
      ? { ok: true, value: reading(data.sitting, data.elapsed_sec, now()) }
      : { ok: false, refused: described(error) };
  });
}
