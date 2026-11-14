import { useEffect, useMemo, useState } from 'react'

import { learnerLog, learnerView, loadSnapshot, type Snapshot } from '@climb/core'

import { useKnowledge } from '@/knowledge/context'

/** The catalog, the focus and the boards one user's copy builds, as the phone's store builds them. */
export function useLearner() {
  const k = useKnowledge()
  const now = useNow()
  const raw = useMemo(
    () => (k.snapshot ? loadSnapshot(k.snapshot as Snapshot) : null),
    [k.snapshot],
  )
  const log = useMemo(() => learnerLog(k.records), [k.records])
  const learner = useMemo(() => learnerView(raw, log), [raw, log])
  return {
    ready: k.ready,
    ...learner,
    now,
    newLimit: learner.limitAt(now),
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
