import {
  pyJson,
  syncPass,
  type components,
  type Cursor,
  type Outgoing,
  type SyncStore,
  type SyncTransport,
} from '@algo-coach/core';

import { writeCatalog } from './courses-cache';
import * as DB from './db';
import { call } from './engine';
import type { Settings } from './settings';

export interface SyncResult {
  user: string; // whose log the engine answered with
  coursesChanged: boolean;
  progressChanged: boolean;
  pushed: number;
}

// learn's line kinds, as the engine's sync names them, against the local tables
const KIND: Record<DB.Table, string> = {
  attempts: 'attempt',
  sessions: 'session',
  statuses: 'status',
  focus: 'focus',
  lessons: 'lesson',
  certs: 'cert',
  setting_changes: 'setting',
  raises: 'raise',
  orders: 'order',
};
const TABLE = Object.fromEntries(Object.entries(KIND).map(([table, kind]) => [kind, table])) as Record<
  string,
  DB.Table
>;

type Synced = components['schemas']['Synced'];
type Held = Outgoing & { row: DB.Pending };

// the phone's copy, in SQLite, as the core's sync reads and writes it
function store(user: string | null): SyncStore<Held> {
  return {
    etag: () => DB.getMeta('snapshot_etag'),
    putSnapshot: async (text, etag) => {
      await writeCatalog(text);
      await DB.setMeta('snapshot_etag', etag);
    },
    outbox: async () =>
      (await DB.pending()).map((row) => ({
        kind: KIND[row.table],
        client_id: row.client_id,
        line: JSON.parse(row.line) as Record<string, unknown>,
        row,
      })),
    cursor: async () => JSON.parse((await DB.getMeta(DB.cursorKey(user))) ?? '{}') as Cursor,
    // a copy keyed to another user must not take this log's records: the next
    // launch keys it again. A copy from before the owner was kept takes the reply's
    checkUser: async (answered) => {
      if (user && user !== answered) throw new Error('the token names another user than this copy');
    },
    commit: async (sent, received, answered, cursor) => {
      await DB.markSent(sent.map((one) => one.row));
      let merged = 0;
      for (const line of received) {
        const table = TABLE[line.kind];
        if (table && (await DB.merged(table, line.client_id, line.device, pyJson(line.rest), line.t))) merged++;
      }
      await DB.setMeta(DB.cursorKey(answered), JSON.stringify(cursor));
      return merged;
    },
  };
}

function transport(s: Settings, token: string): SyncTransport {
  return {
    snapshot: async (etag) => {
      const content = await call(s.origin, '/knowledge/snapshot', {
        token,
        headers: etag ? { 'if-none-match': etag } : {},
      });
      if (content.status === 304) return null;
      return { text: await content.text(), etag: content.headers.get('etag') ?? '' };
    },
    sync: async (records, since) => {
      const answer = (await (
        await call(s.origin, '/knowledge/sync', { token, body: { device: s.device, records, since } })
      ).json()) as Synced;
      return answer;
    },
  };
}

/** One pass of the sync both clients run: `syncPass`, over the phone's copy. */
export async function syncOnce(s: Settings, token: string, user: string | null): Promise<SyncResult> {
  const passed = await syncPass(store(user), transport(s, token));
  return {
    user: passed.user,
    coursesChanged: passed.contentChanged,
    progressChanged: passed.logChanged,
    pushed: passed.stored,
  };
}
