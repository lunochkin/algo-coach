import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { newRecord, syncDelay, SyncLoop, syncPass, type Outgoing, type SyncStore, type SyncTransport } from './index';

function memoryStore(held: string[] = [], user = 'u-4f9c2a') {
  const state = {
    etag: null as string | null,
    snapshot: null as string | null,
    outbox: [{ kind: 'attempt', client_id: 'c1', line: { t: '2026-11-10T08:00:00+00:00' } }] as Outgoing[],
    sent: [] as string[],
    held: new Set(held),
    cursor: {} as Record<string, number>,
  };
  const store: SyncStore<Outgoing> = {
    etag: async () => state.etag,
    putSnapshot: async (text, etag) => {
      state.snapshot = text;
      state.etag = etag;
    },
    outbox: async () => state.outbox,
    cursor: async () => state.cursor,
    checkUser: async (one) => {
      if (one !== user) throw new Error('another user');
    },
    commit: async (sent, received, _user, cursor) => {
      state.sent.push(...sent.map((one) => one.client_id));
      state.cursor = cursor;
      let n = 0;
      for (const one of received) if (!state.held.has(one.client_id)) (state.held.add(one.client_id), n++);
      return n;
    },
  };
  return { store, state };
}

const record = (client_id: string) => ({ kind: 'attempt', client_id, device: 'phone', t: '2026-11-10T09:00:00+00:00' });

function transport(records: Record<string, unknown>[], user_id = 'u-4f9c2a', snapshot: string | null = null) {
  const sent: Record<string, unknown>[][] = [];
  const one: SyncTransport = {
    snapshot: async () => (snapshot === null ? null : { text: snapshot, etag: '"e1"' }),
    sync: async (lines) => {
      sent.push(lines);
      return { user_id, records, cursor: { attempts: 7 } };
    },
  };
  return { one, sent };
}

describe('one sync pass', () => {
  it('sends the outbox with each kind and id, and keeps what the copy does not hold', async () => {
    const { store, state } = memoryStore(['c2']);
    const { one, sent } = transport([record('c2'), record('c3'), { kind: 'attempt' }]);

    const passed = await syncPass(store, one);

    expect(sent[0]).toEqual([{ t: '2026-11-10T08:00:00+00:00', kind: 'attempt', client_id: 'c1' }]);
    expect(state.sent).toEqual(['c1']);
    expect(state.cursor).toEqual({ attempts: 7 });
    expect(passed).toMatchObject({ contentChanged: false, logChanged: true });
  });

  it('keeps a snapshot the engine sent with its tag', async () => {
    const { store, state } = memoryStore();
    await syncPass(store, transport([], 'u-4f9c2a', '{"courses": []}').one);
    expect([state.snapshot, state.etag]).toEqual(['{"courses": []}', '"e1"']);
  });

  it('keeps nothing from a reply naming another user', async () => {
    const { store, state } = memoryStore();
    await expect(syncPass(store, transport([record('c3')], 'u-b71e03').one)).rejects.toThrow('another user');
    expect(state.sent).toEqual([]);
  });
});

describe('the sync loop', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('keeps the earliest deadline asked for', async () => {
    const run = vi.fn(async () => {});
    const loop = new SyncLoop(run);
    loop.request(0);
    loop.request(10_000);
    await vi.advanceTimersByTimeAsync(0);
    expect(run).toHaveBeenCalledTimes(1);
  });

  it('lets no later request push a sync already due', async () => {
    const run = vi.fn(async () => {});
    const loop = new SyncLoop(run);
    loop.request(10_000);
    await vi.advanceTimersByTimeAsync(6_000);
    loop.request(10_000);
    await vi.advanceTimersByTimeAsync(4_000);
    expect(run).toHaveBeenCalledTimes(1);
  });

  it('runs once more after a run that was asked for again', async () => {
    let release = () => {};
    const run = vi.fn(() => new Promise<void>((done) => (release = done)));
    const loop = new SyncLoop(run);
    const first = loop.now();
    void loop.now();
    release();
    await vi.advanceTimersByTimeAsync(0);
    release();
    await first;
    expect(run).toHaveBeenCalledTimes(2);
  });

  it('tries a failed sync again, unless the failure says not to', async () => {
    const run = vi.fn(async () => {
      throw new Error('offline');
    });
    await new SyncLoop(run).now();
    await vi.advanceTimersByTimeAsync(30_000);
    expect(run).toHaveBeenCalledTimes(2);

    const signedOut = vi.fn(async () => {
      throw new Error('signed out');
    });
    await new SyncLoop(signedOut, () => false).now();
    await vi.advanceTimersByTimeAsync(60_000);
    expect(signedOut).toHaveBeenCalledTimes(1);
  });
});

describe('a new record', () => {
  it('is stamped in whole seconds, as the engine stamps it', () => {
    expect(newRecord.raise().t).toMatch(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00$/);
    expect(newRecord.focus(null)).toMatchObject({ course: null, strict: false });
  });

  it('waits for the next answers before an answer is sent, and sends the rest at once', () => {
    expect(syncDelay('attempt')).toBe(10_000);
    expect(syncDelay('focus')).toBe(0);
  });
});
