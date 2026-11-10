import { syncedLine } from '@algo-coach/core'
import { deleteDB, openDB, type DBSchema, type IDBPDatabase } from 'idb'

// the browser's copy of the content and of one user's log: `knowledge.md`,
// A client's store

// a browser carries no stable device name
export const DEVICE = 'web'

export type Cursor = Record<string, number>
export type Line = Record<string, unknown>

/** One record of the log as the copy holds it: learn's line, apart from its kind and ids. */
export interface Held {
  client_id: string
  kind: string
  device: string
  t: string
  line: Line
  pending: 0 | 1 // in the outbox: the engine has not acknowledged it
}

/** What the copy asks the engine for, so a test can answer in its place. */
export interface Transport {
  // null where the snapshot the copy holds still stands
  snapshot(etag: string | null): Promise<{ text: string; etag: string } | null>
  sync(records: Line[], since: Cursor): Promise<{ user_id: string; records: Line[]; cursor: Cursor }>
}

interface Schema extends DBSchema {
  meta: { key: string; value: string }
  records: { key: string; value: Held; indexes: { pending: number } }
}

export interface Synced {
  contentChanged: boolean
  logChanged: boolean
}

/** The database one user's copy lives in, so another account never reads it. */
export const copyName = (user: string) => `algo-coach-knowledge:${user}`

export class Copy {
  private readonly db: IDBPDatabase<Schema>
  private readonly transport: Transport
  readonly user: string

  private constructor(db: IDBPDatabase<Schema>, transport: Transport, user: string) {
    this.db = db
    this.transport = transport
    this.user = user
  }

  static async open(user: string, transport: Transport): Promise<Copy> {
    const db = await openDB<Schema>(copyName(user), 1, {
      upgrade(d) {
        d.createObjectStore('meta')
        d.createObjectStore('records', { keyPath: 'client_id' }).createIndex('pending', 'pending')
      },
    })
    return new Copy(db, transport, user)
  }

  snapshot(): Promise<string | undefined> {
    return this.db.get('meta', 'snapshot')
  }

  async records(): Promise<Held[]> {
    const all = await this.db.getAll('records')
    return all.sort((a, b) => a.t.localeCompare(b.t))
  }

  /** When the last sync finished, as the copy kept it between visits. */
  lastSync(): Promise<string | undefined> {
    return this.db.get('meta', 'last_sync')
  }

  async outbox(): Promise<number> {
    return this.db.countFromIndex('records', 'pending', 1)
  }

  /** Keeps a record the user made here, in the outbox until the engine has it. */
  async add(kind: string, line: Line): Promise<Held> {
    const t = typeof line.t === 'string' ? line.t : new Date().toISOString()
    const held: Held = { client_id: crypto.randomUUID(), kind, device: DEVICE, t, line: { ...line, t }, pending: 1 }
    await this.db.put('records', held)
    return held
  }

  /**
   * Fetches the content where it changed, sends the outbox, and keeps every
   * record the engine returns that the copy does not hold yet.
   */
  async sync(): Promise<Synced> {
    const result: Synced = { contentChanged: false, logChanged: false }
    const content = await this.transport.snapshot((await this.db.get('meta', 'etag')) ?? null)
    if (content) {
      const tx = this.db.transaction('meta', 'readwrite')
      await Promise.all([tx.store.put(content.text, 'snapshot'), tx.store.put(content.etag, 'etag'), tx.done])
      result.contentChanged = true
    }

    const sending = await this.db.getAllFromIndex('records', 'pending', 1)
    const since = JSON.parse((await this.db.get('meta', 'cursor')) ?? '{}') as Cursor
    const lines = sending.map((one) => ({ ...one.line, kind: one.kind, client_id: one.client_id }))
    const answer = await this.transport.sync(lines, since)
    // the database is named by the user, so a reply for another one is a bug
    if (answer.user_id !== this.user) throw new Error('the session names another user than this copy')

    const tx = this.db.transaction(['records', 'meta'], 'readwrite')
    const records = tx.objectStore('records')
    // a refused record names content the engine does not hold, and sending it again changes nothing
    for (const one of sending) await records.put({ ...one, pending: 0 })
    for (const record of answer.records) {
      const one = syncedLine(record)
      if (!one || (await records.get(one.client_id))) continue
      await records.put({ client_id: one.client_id, kind: one.kind, device: one.device, t: one.t, line: one.rest, pending: 0 })
      result.logChanged = true
    }
    await tx.objectStore('meta').put(JSON.stringify(answer.cursor), 'cursor')
    await tx.objectStore('meta').put(new Date().toISOString(), 'last_sync')
    await tx.done
    return result
  }

  close() {
    this.db.close()
  }
}

/** Deletes one user's copy: the content, the log and the cursor. */
export async function eraseCopy(user: string) {
  await deleteDB(copyName(user))
}
