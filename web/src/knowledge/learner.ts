import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  Board,
  currentFocus,
  learnerCatalog,
  loadSnapshot,
  moduleOrder,
  todayLimit,
  type AttemptRecord,
  type CertRecord,
  type FocusRecord,
  type LessonRecord,
  type OrderRecord,
  type RaiseRecord,
  type SettingRecord,
  type Snapshot,
  type StatusRecord,
} from '@algo-coach/core'

import { linesOf, useKnowledge } from '@/knowledge/context'

/** The catalog, the focus and the boards one user's copy builds, as the phone's store builds them. */
export function useLearner() {
  const k = useKnowledge()
  const now = useNow()
  const raw = useMemo(
    () => (k.snapshot ? loadSnapshot(k.snapshot as Snapshot) : null),
    [k.snapshot],
  )
  const { records } = k
  const log = useMemo(
    () => ({
      attempts: linesOf<AttemptRecord>(records, 'attempt'),
      statuses: linesOf<StatusRecord>(records, 'status'),
      lessons: linesOf<LessonRecord>(records, 'lesson'),
      certs: linesOf<CertRecord>(records, 'cert'),
      focuses: linesOf<FocusRecord>(records, 'focus'),
      settings: linesOf<SettingRecord>(records, 'setting'),
      raises: linesOf<RaiseRecord>(records, 'raise'),
      orders: linesOf<OrderRecord>(records, 'order'),
    }),
    [records],
  )
  const learner = useMemo(() => (raw ? learnerCatalog(raw, log) : null), [raw, log])
  const catalog = learner?.catalog ?? null
  const focus = useMemo(() => (catalog ? currentFocus(log.focuses, catalog) : null), [catalog, log])
  const board = useCallback(
    (only: string | null, include: string | null = null) =>
      catalog ? Board.build(catalog, log.attempts, only, include) : null,
    [catalog, log],
  )
  return {
    ready: k.ready,
    catalog,
    // hidden everywhere but the settings, where they are restored
    archived: learner?.archived ?? [],
    focus,
    board,
    now,
    newLimit: todayLimit(log.settings, log.raises, now),
    order: moduleOrder(log.orders),
    certExams: log.certs,
  }
}

// the moment the counts are read at, moved on each minute: a step falls due
// and a raise ends at the rollover with no record arriving
function useNow(): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 60_000)
    return () => clearInterval(tick)
  }, [])
  return now
}
