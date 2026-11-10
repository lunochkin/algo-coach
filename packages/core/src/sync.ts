import type { CertRecord } from './certs';
import { focusLine, type Focus, type FocusRecord } from './focus';
import type { OrderRecord } from './order';
import { NEW_STEP } from './queue';
import { isoNow } from './records';
import type { SettingName, SettingRecord } from './settings';
import { syncedLine, type SyncedLine } from './synced';
import type { CourseStatus, LessonRecord, RaiseRecord, SessionRecord, StatusRecord } from './types';

// a client's sync with the engine, for every platform: `knowledge.md`, A
// client's store. Each client keeps the copy its own way and implements
// `SyncStore`; the order of the steps and every decision live here

export type Cursor = Record<string, number>;
export type Line = Record<string, unknown>;

/** A record in the outbox: its kind, its id and learn's line. */
export interface Outgoing {
  kind: string;
  client_id: string;
  line: Line;
}

/** The engine's two knowledge endpoints, as a client reaches them. */
export interface SyncTransport {
  // null where the snapshot the copy holds still stands
  snapshot(etag: string | null): Promise<{ text: string; etag: string } | null>;
  sync(records: Line[], since: Cursor): Promise<{ user_id: string; records: Line[]; cursor: Cursor; stored?: number }>;
}

/** What a sync reads from and writes to the copy a client keeps. */
export interface SyncStore<O extends Outgoing> {
  etag(): Promise<string | null>;
  putSnapshot(text: string, etag: string): Promise<void>;
  outbox(): Promise<O[]>;
  cursor(): Promise<Cursor>;
  // throws where the reply names a user the copy is not keyed to
  checkUser(user: string): Promise<void>;
  // marks `sent` sent, keeps each line the copy does not hold, and the cursor
  // under `user`; how many lines were new
  commit(sent: O[], received: SyncedLine[], user: string, cursor: Cursor): Promise<number>;
}

export interface Passed {
  user: string;
  contentChanged: boolean;
  logChanged: boolean;
  stored: number;
}

/**
 * Fetches the content where it changed, sends the outbox, and keeps every
 * record the engine returns that the copy does not hold yet.
 */
export async function syncPass<O extends Outgoing>(store: SyncStore<O>, transport: SyncTransport): Promise<Passed> {
  const content = await transport.snapshot(await store.etag());
  if (content) await store.putSnapshot(content.text, content.etag);

  const sending = await store.outbox();
  const lines = sending.map((one) => ({ ...one.line, kind: one.kind, client_id: one.client_id }));
  const answer = await transport.sync(lines, await store.cursor());
  await store.checkUser(answer.user_id);

  // a refused record names content the engine does not hold, and sending it
  // again changes nothing, so every record sent leaves the outbox
  const received = answer.records.map(syncedLine).filter((one): one is SyncedLine => one !== null);
  const merged = await store.commit(sending, received, answer.user_id, answer.cursor);
  return { user: answer.user_id, contentChanged: content !== null, logChanged: merged > 0, stored: answer.stored ?? 0 };
}

// an answer waits for the ones after it, so a run of answers travels in one
// upload; every other record changes what another device serves
export const ANSWER_DELAY = 10_000;
export const syncDelay = (kind: string): number => (kind === 'attempt' ? ANSWER_DELAY : 0);
export const SYNC_RETRY = 30_000;

/**
 * Runs a client's sync one at a time. A request during a run runs it again
 * after; the earliest deadline asked for stands; a failure `retries` accepts
 * is tried again after `retryMs`.
 */
export class SyncLoop {
  private timer: ReturnType<typeof setTimeout> | null = null;
  private dueAt: number | null = null;
  private retry: ReturnType<typeof setTimeout> | null = null;
  private running: Promise<void> | null = null;
  private again = false;

  private run: () => Promise<void>;
  private readonly retries: (error: unknown) => boolean;
  private readonly retryMs: number;

  constructor(run: () => Promise<void>, retries: (error: unknown) => boolean = () => true, retryMs = SYNC_RETRY) {
    this.run = run;
    this.retries = retries;
    this.retryMs = retryMs;
  }

  /** Runs `run` from the next sync on: a client whose pass is rebuilt hands the newest one here. */
  use(run: () => Promise<void>): void {
    this.run = run;
  }

  /** A sync within `delayMs`, unless one is due sooner already. */
  request(delayMs = 0): void {
    const at = Date.now() + delayMs;
    if (this.timer && this.dueAt !== null && this.dueAt <= at) return;
    if (this.timer) clearTimeout(this.timer);
    this.dueAt = at;
    this.timer = setTimeout(() => {
      this.timer = null;
      this.dueAt = null;
      void this.now();
    }, delayMs);
  }

  /** Syncs now, or after the run in progress; settles when the copy is synced or the sync failed. */
  now(): Promise<void> {
    if (this.running) {
      this.again = true;
      return this.running;
    }
    if (this.retry) clearTimeout(this.retry);
    this.retry = null;
    this.running = (async () => {
      let failed: unknown = null;
      do {
        this.again = false;
        failed = null;
        try {
          await this.run();
        } catch (error) {
          failed = error;
        }
      } while (this.again && failed === null);
      this.running = null;
      if (failed !== null && this.retries(failed)) this.retry = setTimeout(() => void this.now(), this.retryMs);
    })();
    return this.running;
  }

  /** Stops every timer, as a client leaving the page or signing out does. */
  stop(): void {
    for (const one of [this.timer, this.retry]) if (one) clearTimeout(one);
    this.timer = this.retry = null;
    this.dueAt = null;
  }
}

// each record a user makes, stamped as the engine stamps it: whole seconds,
// `+00:00`, so two clients' records sort the same
export const newRecord = {
  status: (course: string, status: CourseStatus): StatusRecord => ({ t: isoNow(), course, status }),
  focus: (f: Focus | null): FocusRecord => ({ t: isoNow(), ...focusLine(f) }),
  lesson: (course: string, lesson: string, status: LessonRecord['status']): LessonRecord => ({
    t: isoNow(),
    course,
    lesson,
    status,
  }),
  cert: (rec: Omit<CertRecord, 't'>): CertRecord => ({ t: isoNow(), ...rec }),
  session: (mode: SessionRecord['mode'], score: number, n: number): SessionRecord => ({ t: isoNow(), mode, score, n }),
  raise: (): RaiseRecord => ({ t: isoNow(), n: NEW_STEP }),
  setting: (name: SettingName, n: number): SettingRecord => ({ t: isoNow(), name, n }),
  order: (courses: string[]): OrderRecord => ({ t: isoNow(), courses }),
};
