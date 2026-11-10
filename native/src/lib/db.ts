import * as Crypto from 'expo-crypto';
import * as SQLite from 'expo-sqlite';

import {
  pyJson,
  type AttemptRecord,
  type CertRecord,
  type FocusRecord,
  type LessonRecord,
  type OrderRecord,
  type RaiseRecord,
  type SettingRecord,
  type SessionRecord,
  type StatusRecord,
} from '@algo-coach/core';

export type Table = 'attempts' | 'sessions' | 'statuses' | 'focus' | 'lessons' | 'certs' | 'setting_changes' | 'raises' | 'orders';
export const TABLES: Table[] = ['attempts', 'sessions', 'statuses', 'focus', 'lessons', 'certs', 'setting_changes', 'raises', 'orders'];

let opened: Promise<SQLite.SQLiteDatabase> | null = null;

export function db(): Promise<SQLite.SQLiteDatabase> {
  // a file of its own: learn's app kept GitHub's bookkeeping in learn.db
  opened ??= (async () => {
    const d = await SQLite.openDatabaseAsync('algo-coach.db');
    await d.execAsync('PRAGMA journal_mode = WAL;');
    for (const table of TABLES) {
      await d.execAsync(`
        CREATE TABLE IF NOT EXISTS ${table} (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          client_id TEXT NOT NULL UNIQUE,
          path TEXT NOT NULL,
          line TEXT NOT NULL,
          t TEXT NOT NULL,
          pending INTEGER NOT NULL,
          owner TEXT
        );
      `);
      // a copy written before the owner was kept: its rows are adopted once the user is known
      const columns = await d.getAllAsync<{ name: string }>(`PRAGMA table_info(${table})`);
      if (!columns.some((c) => c.name === 'owner')) await d.execAsync(`ALTER TABLE ${table} ADD COLUMN owner TEXT`);
    }
    await d.execAsync('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);');
    return d;
  })();
  return opened;
}

// the signed-in user, whose rows alone are read, written and sent: `knowledge.md`, A client's store
let owner: string | null = null;

export function setOwner(user: string | null) {
  owner = user;
}

interface Row {
  id: number;
  client_id: string;
  path: string;
  line: string;
  t: string;
  pending: number;
}

async function lines<T>(table: Table): Promise<T[]> {
  const rows = await (await db()).getAllAsync<Row>(`SELECT line FROM ${table} WHERE owner IS ? ORDER BY t, id`, owner);
  return rows.map((r) => JSON.parse(r.line) as T);
}

export const allAttempts = () => lines<AttemptRecord>('attempts');
export const allSessions = () => lines<SessionRecord>('sessions');
export const allStatuses = () => lines<StatusRecord>('statuses');
export const allFocus = () => lines<FocusRecord>('focus');
export const allCerts = () => lines<CertRecord>('certs');
export const allLessons = () => lines<LessonRecord>('lessons');
export const allSettings = () => lines<SettingRecord>('setting_changes');
export const allRaises = () => lines<RaiseRecord>('raises');
export const allOrders = () => lines<OrderRecord>('orders');

/** Gives the rows written before any owner was kept to `user`, the account whose token wrote them. */
export async function adopt(user: string) {
  const d = await db();
  for (const table of TABLES) await d.runAsync(`UPDATE ${table} SET owner = ? WHERE owner IS NULL`, user);
}

/** Deletes `user`'s copy: every row, and the cursor its sync read from. */
export async function erase(user: string | null) {
  const d = await db();
  await d.withExclusiveTransactionAsync(async (tx) => {
    for (const table of TABLES) await tx.runAsync(`DELETE FROM ${table} WHERE owner IS ?`, user);
    await tx.runAsync('DELETE FROM meta WHERE key = ?', cursorKey(user));
  });
}

export const cursorKey = (user: string | null) => (user ? `sync_cursor:${user}` : 'sync_cursor');

export async function addLocal(
  table: Table,
  path: string,
  rec: AttemptRecord | SessionRecord | StatusRecord | FocusRecord | LessonRecord | CertRecord | SettingRecord | RaiseRecord | OrderRecord,
) {
  // minted once, here, so a retried upload is recognised by the engine
  await (
    await db()
  ).runAsync(
    `INSERT INTO ${table} (client_id, path, line, t, pending, owner) VALUES (?, ?, ?, ?, 1, ?)`,
    Crypto.randomUUID(),
    path,
    pyJson(rec),
    rec.t,
    owner,
  );
}

export interface Pending {
  table: Table;
  client_id: string;
  line: string;
}

export async function pending(): Promise<Pending[]> {
  const d = await db();
  const found: Pending[] = [];
  for (const table of TABLES) {
    const rows = await d.getAllAsync<Row>(`SELECT client_id, line FROM ${table} WHERE pending = 1 AND owner IS ? ORDER BY id`, owner);
    found.push(...rows.map((r) => ({ table, client_id: r.client_id, line: r.line })));
  }
  return found;
}

export async function markSent(sent: Pending[]) {
  const d = await db();
  await d.withExclusiveTransactionAsync(async (tx) => {
    for (const one of sent) {
      await tx.runAsync(`UPDATE ${one.table} SET pending = 0 WHERE client_id = ?`, one.client_id);
    }
  });
}

/** A record the engine returned, kept unless this device already holds it. */
export async function merged(table: Table, clientId: string, device: string, line: string, t: string) {
  const d = await db();
  const r = await d.runAsync(
    `INSERT OR IGNORE INTO ${table} (client_id, path, line, t, pending, owner) VALUES (?, ?, ?, ?, 0, ?)`,
    clientId,
    device,
    line,
    t,
    owner,
  );
  return r.changes > 0;
}

export async function getMeta(key: string): Promise<string | null> {
  const row = await (
    await db()
  ).getFirstAsync<{ value: string }>('SELECT value FROM meta WHERE key = ?', key);
  return row?.value ?? null;
}

export async function setMeta(key: string, value: string) {
  await (await db()).runAsync('INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)', key, value);
}
