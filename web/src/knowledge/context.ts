import { createContext, useContext } from 'react'

import type { Held, Line } from '@/knowledge/copy'

export interface SyncState {
  running: boolean
  error: string | null
}

export interface Knowledge {
  // false until the copy is read: a page then shows what the device held
  ready: boolean
  snapshot: unknown
  records: Held[]
  outbox: number
  sync: SyncState
  resync: () => Promise<void>
  /** Keeps a record the user made, and sends it as `knowledge.md` times it. */
  add: (kind: string, line: Line) => Promise<void>
  /** Sends the outbox, then deletes the copy; the number left unsent where `force` is false. */
  leave: (force: boolean) => Promise<number>
}

export const KnowledgeContext = createContext<Knowledge | null>(null)

export function useKnowledge(): Knowledge {
  const knowledge = useContext(KnowledgeContext)
  if (!knowledge) throw new Error('useKnowledge outside the KnowledgeProvider')
  return knowledge
}

/** The lines of one kind, in the shape learn wrote them and the core reads. */
export function linesOf<T>(records: Held[], kind: string): T[] {
  return records.filter((one) => one.kind === kind).map((one) => one.line as unknown as T)
}

/** A page's reading of the copy, in the states `Loaded` renders. */
export function loadedFrom<T>(k: Knowledge, data: T | undefined) {
  const shown = k.ready ? data : undefined
  return {
    data: shown,
    // a copy holding nothing yet fails with its sync; one holding something reads on
    error: shown === undefined && k.sync.error ? k.sync.error : undefined,
    retry: () => void k.resync(),
  }
}
