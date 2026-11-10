import { pyJson, syncedLine, type components } from '@algo-coach/core';

import { writeCatalog } from './courses-cache';
import * as DB from './db';
import { call } from './engine';
import type { Settings } from './settings';

export interface SyncResult {
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
  limits: 'limit',
  raises: 'raise',
};
const TABLE = Object.fromEntries(Object.entries(KIND).map(([table, kind]) => [kind, table])) as Record<
  string,
  DB.Table
>;

// the sync's request and reply, as the engine's OpenAPI schema states them
type Upload = components['schemas']['Upload'];
type Synced = components['schemas']['Synced'];


/**
 * Fetches the content when it changed, sends this device's pending records, and
 * keeps every record the engine returns that this device does not hold yet.
 */
export async function syncOnce(s: Settings, token: string): Promise<SyncResult> {
  const result: SyncResult = { coursesChanged: false, progressChanged: false, pushed: 0 };

  const tag = await DB.getMeta('snapshot_etag');
  const content = await call(s.origin, '/knowledge/snapshot', {
    token,
    headers: tag ? { 'if-none-match': tag } : {},
  });
  if (content.status !== 304) {
    await writeCatalog(await content.text());
    await DB.setMeta('snapshot_etag', content.headers.get('etag') ?? '');
    result.coursesChanged = true;
  }

  const sending = await DB.pending();
  const since = JSON.parse((await DB.getMeta('sync_cursor')) ?? '{}') as Record<string, number>;
  const records = sending.map((one) => ({ ...JSON.parse(one.line), kind: KIND[one.table], client_id: one.client_id }));
  const upload: Upload = { device: s.device, records, since };
  const answer = (await (await call(s.origin, '/knowledge/sync', { token, body: upload })).json()) as Synced;

  // a refused record names content the engine does not hold, and sending it again changes nothing
  await DB.markSent(sending);
  result.pushed = answer.stored;
  for (const record of answer.records) {
    const line = syncedLine(record);
    const table = line && TABLE[line.kind];
    if (line && table && (await DB.merged(table, line.client_id, line.device, pyJson(line.rest), line.t))) {
      result.progressChanged = true;
    }
  }
  await DB.setMeta('sync_cursor', JSON.stringify(answer.cursor));
  return result;
}
