import { useState } from 'react'

import {
  FORECAST_HEADING,
  FORECAST_NOTE,
  forecastBarLabel,
  type ForecastView,
} from '@algo-coach/core'

import { Panel } from '@/components/Panel'
import { SectionHeading } from '@/components/SectionHeading'
import { cn } from '@/lib/utils'

const HEIGHT = 64

// a column per learning day; the readout above names the hovered day, and the
// list under it carries every count for a reader the bars do not reach
export function ReviewForecast({ view }: { view: ForecastView }) {
  const [hover, setHover] = useState<number | null>(null)
  const shown = hover === null ? null : view.bars[hover]
  return (
    <section className="space-y-stack">
      <SectionHeading title={FORECAST_HEADING} />
      <Panel>
        <p className="text-meta text-muted-foreground tabular-nums" aria-live="polite">
          {shown ? forecastBarLabel(shown.day, shown.reviews) : view.summary}
        </p>
        <div className="flex items-end gap-0.5" style={{ height: HEIGHT + 16 }} aria-hidden="true">
          {view.bars.map((bar, i) => (
            <div
              key={i}
              className="flex h-full flex-1 flex-col items-center justify-end"
              onPointerEnter={() => setHover(i)}
              onPointerLeave={() => setHover(null)}
            >
              <span className="text-micro text-muted-foreground tabular-nums">
                {bar.labelled ? bar.reviews : ' '}
              </span>
              <div
                className={cn(
                  'w-full max-w-6 rounded-t',
                  bar.today ? 'bg-foreground' : 'bg-muted-foreground',
                  hover !== null && hover !== i && 'opacity-50',
                )}
                style={{
                  height: view.max
                    ? Math.max(bar.reviews ? 2 : 0, (bar.reviews / view.max) * HEIGHT)
                    : 0,
                }}
              />
            </div>
          ))}
        </div>
        <div
          className="flex justify-between border-t pt-1 text-micro text-muted-foreground"
          aria-hidden="true"
        >
          <span>{view.first}</span>
          <span>{view.last}</span>
        </div>
        <ul className="sr-only">
          {view.bars.map((bar, i) => (
            <li key={i}>{forecastBarLabel(bar.day, bar.reviews)}</li>
          ))}
        </ul>
        <p className="text-meta text-muted-foreground">{FORECAST_NOTE}</p>
      </Panel>
    </section>
  )
}
