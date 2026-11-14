import {
  isoNow,
  syncPass,
  type Cursor,
  type Line,
  type SyncStore,
  type SyncTransport,
} from '@climb/core'
import { deleteDB, openDB, type DBSchema, type IDBPDatabase } from 'idb'

// the browser's copy of the content and of one user's log: `knowledge.md`,
// A client's store

// a browser carries no stable device name
export const DEVICE = 'web'

export type { Cursor, Line }

/** One record of the log as the copy holds it: learn's line, apart from its kind and ids. */
export interface Held {
  client_id: string
  kind: string
  device: string
  t: string
  line: Line
  pending: 0 | 1 // in the outbox: the engine has not acknowledged it
}

// what the copy asks the engine for, so a test can answer in its place
export type Transport = SyncTransport

interface Schema extends DBSchema {
  meta: { key: string; value: string }
  records: { key: string; value: Held; indexes: { pending: number } }
}

export interface Synced {
  contentChanged: boolean
  logChanged: boolean
}

/** The database one user's copy lives in, so another account never reads it. */
export const copyName = (user: string) => `climb-knowledge:${user}`

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
  async add(kind: string, record: object): Promise<Held> {
    const line = record as Line
    const t = typeof line.t === 'string' ? line.t : isoNow()
    const held: Held = {
      client_id: crypto.randomUUID(),
      kind,
      device: DEVICE,
      t,
      line: { ...line, t },
      pending: 1,
    }
    await this.db.put('records', held)
    return held
  }

  /** Syncs with the engine, through the pass both clients run: `syncPass`. */
  async sync(): Promise<Synced> {
    const passed = await syncPass(this.store(), this.transport)
    return { contentChanged: passed.contentChanged, logChanged: passed.logChanged }
  }

  private store(): SyncStore<Held> {
    const db = this.db
    return {
      etag: async () => (await db.get('meta', 'etag')) ?? null,
      putSnapshot: async (text, etag) => {
        const tx = db.transaction('meta', 'readwrite')
        await Promise.all([tx.store.put(text, 'snapshot'), tx.store.put(etag, 'etag'), tx.done])
      },
      outbox: () => db.getAllFromIndex('records', 'pending', 1),
      cursor: async () => JSON.parse((await db.get('meta', 'cursor')) ?? '{}') as Cursor,
      // the database is named by the user, so a reply for another one is a bug
      checkUser: async (user) => {
        if (user !== this.user) throw new Error('the session names another user than this copy')
      },
      // one transaction, so a sync either lands whole or not at all
      commit: async (sent, received, _user, cursor) => {
        const tx = db.transaction(['records', 'meta'], 'readwrite')
        const records = tx.objectStore('records')
        for (const one of sent) await records.put({ ...one, pending: 0 })
        let merged = 0
        for (const one of received) {
          if (await records.get(one.client_id)) continue
          await records.put({
            client_id: one.client_id,
            kind: one.kind,
            device: one.device,
            t: one.t,
            line: one.rest,
            pending: 0,
          })
          merged++
        }
        await tx.objectStore('meta').put(JSON.stringify(cursor), 'cursor')
        await tx.objectStore('meta').put(new Date().toISOString(), 'last_sync')
        await tx.done
        return merged
      },
    }
  }

  close() {
    this.db.close()
  }
}

/** Deletes one user's copy: the content, the log and the cursor. */
export async function eraseCopy(user: string) {
  await deleteDB(copyName(user))
}
