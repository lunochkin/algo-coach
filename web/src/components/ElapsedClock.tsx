import { useEffect, useState } from 'react'

type Props = {
  // the engine's reading, and the moment the page received it
  elapsedSec: number
  receivedAt: number
  running: boolean
}

// its own component: it re-renders every second, and the editor beside it
// must not
export function ElapsedClock({ elapsedSec, receivedAt, running }: Props) {
  const [now, setNow] = useState(() => performance.now())

  useEffect(() => {
    if (!running) return
    const tick = setInterval(() => setNow(performance.now()), 1000)
    return () => clearInterval(tick)
  }, [running])

  // counted on from the engine's number with the page's monotonic clock, so a
  // browser clock set wrong moves nothing
  const shown = running ? elapsedSec + Math.max(0, now - receivedAt) / 1000 : elapsedSec

  return (
    <span className="font-mono text-lg tabular-nums" aria-label="Elapsed time">
      {formatted(shown)}
    </span>
  )
}

function formatted(seconds: number): string {
  const whole = Math.floor(seconds)
  const hours = Math.floor(whole / 3600)
  const minutes = Math.floor((whole % 3600) / 60)
  const rest = String(whole % 60).padStart(2, '0')
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${rest}` : `${minutes}:${rest}`
}
