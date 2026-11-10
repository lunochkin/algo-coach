import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

import { SyncLoop, syncDelay } from '@algo-coach/core'

import { api, LOGIN } from '@/api/client'
import { Copy, eraseCopy, type Held } from '@/knowledge/copy'
import { KnowledgeContext, type Knowledge, type SyncState } from '@/knowledge/context'
import { engine } from '@/knowledge/transport'

export function KnowledgeProvider({ children }: { children: ReactNode }) {
  const copy = useRef<Copy | null>(null)
  const [ready, setReady] = useState(false)
  const [text, setText] = useState<string | undefined>()
  const [records, setRecords] = useState<Held[]>([])
  const [outbox, setOutbox] = useState(0)
  const [sync, setSync] = useState<SyncState>({ running: false, error: null, lastAt: null })

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

  // one pass, reporting its state; the loop decides when it runs: `SyncLoop`
  const runOnce = useCallback(async () => {
    const one = copy.current
    if (!one) return
    setSync((x) => ({ ...x, running: true, error: null }))
    try {
      const synced = await one.sync()
      setSync({ running: false, error: null, lastAt: new Date().toISOString() })
      if (synced.contentChanged || synced.logChanged) await reread(one)
      else setOutbox(await one.outbox())
    } catch (error) {
      setSync((x) => ({ ...x, running: false, error: String(error) }))
      throw error
    }
  }, [reread])
  // the loop lives as long as the provider, and always runs the newest pass
  const [loop] = useState(() => new SyncLoop(async () => {}))
  useEffect(() => loop.use(runOnce), [loop, runOnce])
  useEffect(() => () => loop.stop(), [loop])
  const runSync = useCallback(() => loop.now(), [loop])
  const schedule = useCallback((delay: number) => loop.request(delay), [loop])

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
    async (kind: string, line: object) => {
      const one = copy.current
      if (!one) throw new Error('the copy is not open yet')
      const held = await one.add(kind, line)
      setRecords((xs) => [...xs, held])
      setOutbox((n) => n + 1)
      schedule(syncDelay(kind))
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
