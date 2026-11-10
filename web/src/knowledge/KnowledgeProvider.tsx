import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

import { api, LOGIN } from '@/api/client'
import { Copy, eraseCopy, type Held, type Line } from '@/knowledge/copy'
import { KnowledgeContext, type Knowledge, type SyncState } from '@/knowledge/context'
import { engine } from '@/knowledge/transport'

// answers given in quick succession travel in one upload: `knowledge.md`, A
// client's store
const ANSWER_DELAY = 10_000
const RETRY = 30_000

export function KnowledgeProvider({ children }: { children: ReactNode }) {
  const copy = useRef<Copy | null>(null)
  const [ready, setReady] = useState(false)
  const [text, setText] = useState<string | undefined>()
  const [records, setRecords] = useState<Held[]>([])
  const [outbox, setOutbox] = useState(0)
  const [sync, setSync] = useState<SyncState>({ running: false, error: null, lastAt: null })
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const running = useRef<Promise<void> | null>(null)
  const again = useRef(false)
  const [failedAt, setFailedAt] = useState<number | null>(null)

  const reread = useCallback(async (one: Copy) => {
    const [snapshot, held, pending] = await Promise.all([
      one.snapshot(),
      one.records(),
      one.outbox(),
    ])
    setText(snapshot)
    setRecords(held)
    setOutbox(pending)
  }, [])

  const runSync = useCallback(async (): Promise<void> => {
    const one = copy.current
    if (!one) return
    if (running.current) {
      again.current = true
      return running.current
    }
    running.current = (async () => {
      do {
        again.current = false
        setSync((x) => ({ ...x, running: true, error: null }))
        try {
          const synced = await one.sync()
          setSync({ running: false, error: null, lastAt: new Date().toISOString() })
          if (synced.contentChanged || synced.logChanged) await reread(one)
          else setOutbox(await one.outbox())
        } catch (error) {
          setSync((x) => ({ ...x, running: false, error: String(error) }))
          setFailedAt(Date.now())
          again.current = false
        }
      } while (again.current)
      running.current = null
    })()
    return running.current
  }, [reread])

  // a failed sync is tried again, and the outbox waits for it meanwhile
  useEffect(() => {
    if (failedAt === null) return
    const retry = setTimeout(() => void runSync(), RETRY)
    return () => clearTimeout(retry)
  }, [failedAt, runSync])

  const schedule = useCallback(
    (delay: number) => {
      if (timer.current) {
        if (delay > 0) return // a sync is already due no later than this one
        clearTimeout(timer.current)
      }
      timer.current = setTimeout(() => {
        timer.current = null
        void runSync()
      }, delay)
    },
    [runSync],
  )

  useEffect(() => {
    let gone = false
    void (async () => {
      const { data } = await api.GET('/api/me')
      if (!data || gone) return
      const one = await Copy.open(data.user_id, engine)
      if (gone) return one.close()
      copy.current = one
      const lastAt = (await one.lastSync()) ?? null
      setSync((x) => ({ ...x, lastAt }))
      await reread(one)
      setReady(true)
      schedule(0)
    })()
    // records another device wrote reach the schedule before the next pick
    const visible = () => document.visibilityState === 'visible' && schedule(0)
    document.addEventListener('visibilitychange', visible)
    return () => {
      gone = true
      document.removeEventListener('visibilitychange', visible)
      copy.current?.close()
      copy.current = null
    }
  }, [reread, schedule])

  const add = useCallback(
    async (kind: string, line: Line) => {
      const one = copy.current
      if (!one) throw new Error('the copy is not open yet')
      const held = await one.add(kind, line)
      setRecords((xs) => [...xs, held])
      setOutbox((n) => n + 1)
      // a focus, a status or a setting changes what another device serves
      schedule(kind === 'attempt' ? ANSWER_DELAY : 0)
    },
    [schedule],
  )

  const leave = useCallback(
    async (force: boolean) => {
      const one = copy.current
      if (one) {
        // a forced sign-out follows the warning that the sync failed, so it tries none again
        if (!force) {
          await runSync().catch(() => undefined)
          const unsent = await one.outbox()
          if (unsent) return unsent
        }
        one.close()
        copy.current = null
        await eraseCopy(one.user)
      }
      // revoked on the server, not only dropped from the browser
      await api.DELETE('/api/session')
      window.location.assign(LOGIN)
      return 0
    },
    [runSync],
  )

  // parsed once per snapshot: it weighs megabytes
  const snapshot = useMemo(() => (text ? (JSON.parse(text) as unknown) : null), [text])
  const value = useMemo<Knowledge>(
    () => ({ ready, snapshot, records, outbox, sync, resync: runSync, add, leave }),
    [ready, snapshot, records, outbox, sync, runSync, add, leave],
  )
  return <KnowledgeContext.Provider value={value}>{children}</KnowledgeContext.Provider>
}
