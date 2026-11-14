import { useEffect, useState } from 'react'

import { duration, shownSeconds, ELAPSED_TIME } from '@climb/core'

type Props = {
  // the engine's reading, none while the clock has not run, and the moment
  // the page received it
  elapsedSec: number | null
  receivedAt: number
  running: boolean
}

// its own component: it re-renders every second, and the editor beside it
// must not
export function ElapsedClock({ elapsedSec, receivedAt, running: asked }: Props) {
  const [now, setNow] = useState(() => performance.now())
  // a clock that has not started has nothing to count on from
  const running = asked && elapsedSec !== null

  useEffect(() => {
    if (!running) return
    const tick = setInterval(() => setNow(performance.now()), 1000)
    return () => clearInterval(tick)
  }, [running])

  // counted on with the page's monotonic clock, so a browser clock set wrong
  // moves nothing
  const shown = shownSeconds(elapsedSec, receivedAt, now, running)

  return (
    <span className="font-mono text-heading tabular-nums" aria-label={ELAPSED_TIME}>
      {duration(shown)}
    </span>
  )
}
