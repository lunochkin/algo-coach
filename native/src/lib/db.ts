import * as Crypto from 'expo-crypto';
import * as SQLite from 'expo-sqlite';

import { pyJson, type AttemptRecord, type CertRecord, type FocusRecord, type LessonRecord, type SessionRecord, type StatusRecord } from '@/core';

let opened: Promise<SQLite.SQLiteDatabase> | null = null;

export function db(): Promise<SQLite.SQLiteDatabase> {
  // a file of its own: learn's app kept GitHub's bookkeeping in learn.db
  opened ??= (async () => {
    const d = await SQLite.openDatabaseAsync('algo-coach.db');
    await d.execAsync(`
      PRAGMA journal_mode = WAL;
      CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        line TEXT NOT NULL,
        t TEXT NOT NULL,
        pending INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        line TEXT NOT NULL,
        t TEXT NOT NULL,
        pending INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        line TEXT NOT NULL,
        t TEXT NOT NULL,
        pending INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS focus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        line TEXT NOT NULL,
        t TEXT NOT NULL,
        pending INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        line TEXT NOT NULL,
        t TEXT NOT NULL,
        pending INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS certs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        line TEXT NOT NULL,
        t TEXT NOT NULL,
        pending INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    `);
    return d;
  })();
  return opened;
}

export type Table = 'attempts' | 'sessions' | 'statuses' | 'focus' | 'lessons' | 'certs';
export const TABLES: Table[] = ['attempts', 'sessions', 'statuses', 'focus', 'lessons', 'certs'];

interface Row {
  id: number;
  client_id: string;
  path: string;
  line: string;
  t: string;
  pending: number;
}

/** All attempt records in CLI read order: files sorted by path, lines in file order. */
export async function allAttempts(): Promise<AttemptRecord[]> {
  const rows = await (await db()).getAllAsync<Row>('SELECT line FROM attempts ORDER BY t, id');
  return rows.map((r) => JSON.parse(r.line) as AttemptRecord);
}

export async function allSessions(): Promise<SessionRecord[]> {
  const rows = await (await db()).getAllAsync<Row>('SELECT line FROM sessions ORDER BY t, id');
  return rows
    .map((r) => JSON.parse(r.line) as SessionRecord)
    .sort((a, b) => (a.t < b.t ? -1 : a.t > b.t ? 1 : 0));
}

/** Status records in file order (paths sorted, lines in order), for courseStatuses. */
export async function allStatuses(): Promise<StatusRecord[]> {
  const rows = await (await db()).getAllAsync<Row>('SELECT line FROM statuses ORDER BY t, id');
  return rows.map((r) => JSON.parse(r.line) as StatusRecord);
}

export async function allFocus(): Promise<FocusRecord[]> {
  const rows = await (await db()).getAllAsync<Row>('SELECT line FROM focus ORDER BY t, id');
  return rows.map((r) => JSON.parse(r.line) as FocusRecord);
}

export async function allCerts(): Promise<CertRecord[]> {
  const rows = await (await db()).getAllAsync<Row>('SELECT line FROM certs ORDER BY t, id');
  return rows.map((r) => JSON.parse(r.line) as CertRecord);
}

export async function allLessons(): Promise<LessonRecord[]> {
  const rows = await (await db()).getAllAsync<Row>('SELECT line FROM lessons ORDER BY t, id');
  return rows.map((r) => JSON.parse(r.line) as LessonRecord);
}

export async function addLocal(
  table: Table,
  path: string,
  rec: AttemptRecord | SessionRecord | StatusRecord | FocusRecord | LessonRecord | CertRecord,
) {
  // minted once, here, so a retried upload is recognised by the engine
  await (
    await db()
  ).runAsync(
    `INSERT INTO ${table} (client_id, path, line, t, pending) VALUES (?, ?, ?, ?, 1)`,
    Crypto.randomUUID(),
    path,
    pyJson(rec),
    rec.t,
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
    const rows = await d.getAllAsync<Row>(`SELECT client_id, line FROM ${table} WHERE pending = 1 ORDER BY id`);
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
    `INSERT OR IGNORE INTO ${table} (client_id, path, line, t, pending) VALUES (?, ?, ?, ?, 0)`,
    clientId,
    device,
    line,
    t,
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
