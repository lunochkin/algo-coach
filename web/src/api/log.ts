import { api } from '@/api/client'

// a browser carries no stable device name: `knowledge.md`, A client's store
const DEVICE = 'web'

export type Cursor = Record<string, number>
type Line = Record<string, unknown>

// until the client's store keeps a copy, a page reads the whole log once
export async function readLog(signal: AbortSignal) {
  const { data, error } = await api.POST('/api/knowledge/sync', {
    body: { device: DEVICE, records: [], since: {} },
    signal,
  })
  return data === undefined ? { error } : { data: { records: data.records, cursor: data.cursor } }
}

/** Sends the lines as records of the log, and returns the cursor to send next. */
export async function sendLines(lines: Line[], since: Cursor): Promise<Cursor | null> {
  const records = lines.map((one) => ({
    ...one,
    client_id: crypto.randomUUID(),
    t: new Date().toISOString(),
  }))
  const { data } = await api.POST('/api/knowledge/sync', {
    body: { device: DEVICE, records, since },
  })
  return data?.cursor ?? null
}

/** The lines of one kind, as learn's line shape the core reads. */
export function linesOf<T>(records: Line[], kind: string): T[] {
  return records.filter((one) => one.kind === kind) as unknown as T[]
}
