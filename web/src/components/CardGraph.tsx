import type { CardEdge } from '@climb/core'
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

import { cn } from '@/lib/utils'

// one lane per card that others require, LANE apart, so two edges leaving
// different cards never share a vertical line
const LANE = 10
const INSET = 6
// where an edge meets a row: its title line, whatever the row's height
const TITLE = 22

interface Drawn extends CardEdge {
  lane: number
  y1: number
  y2: number
}

/**
 * The card graph's edges, drawn in a gutter left of the rows: `wireframes.md`,
 * The cards. Rows are found by `data-card` inside `children`, so the sections
 * and panels lay out as any list does and the gutter follows them.
 */
export function CardGraph({
  edges,
  hovered,
  children,
}: {
  edges: CardEdge[]
  hovered: string | null
  children: ReactNode
}) {
  const box = useRef<HTMLDivElement>(null)
  const [drawn, setDrawn] = useState<Drawn[]>([])
  const sources = [...new Set(edges.map((one) => one.from))]
  const gutter = sources.length === 0 ? 0 : INSET * 2 + LANE * sources.length

  useLayoutEffect(() => {
    const el = box.current
    if (!el) return
    const lanes = [...new Set(edges.map((one) => one.from))]
    const measure = () => {
      const top = el.getBoundingClientRect().top
      const ys = new Map<string, number>()
      for (const row of el.querySelectorAll<HTMLElement>('[data-card]')) {
        ys.set(row.dataset.card ?? '', row.getBoundingClientRect().top - top + TITLE)
      }
      setDrawn(
        edges.flatMap((one) => {
          const y1 = ys.get(one.from)
          const y2 = ys.get(one.to)
          return y1 === undefined || y2 === undefined
            ? []
            : [{ ...one, lane: lanes.indexOf(one.from), y1, y2 }]
        }),
      )
    }
    measure()
    const watch = new ResizeObserver(measure)
    watch.observe(el)
    return () => watch.disconnect()
  }, [edges])

  return (
    <div ref={box} className="relative" style={{ paddingLeft: gutter }}>
      {gutter > 0 && (
        <svg
          aria-hidden="true"
          className="pointer-events-none absolute top-0 left-0 h-full"
          style={{ width: gutter }}
        >
          {drawn.map((one) => {
            const x = INSET + LANE * one.lane
            const lit = hovered === null || hovered === one.from || hovered === one.to
            return (
              <g
                key={`${one.from}>${one.to}`}
                className={cn(
                  'transition-opacity',
                  hovered !== null && lit ? 'text-primary' : 'text-muted-foreground',
                  lit ? 'opacity-100' : 'opacity-20',
                )}
              >
                <path
                  d={`M ${gutter} ${one.y1} H ${x} V ${one.y2} H ${gutter}`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                />
                <circle cx={x} cy={one.y1} r={2.5} fill="currentColor" />
                <path
                  d={`M ${gutter - 5} ${one.y2 - 3.5} L ${gutter} ${one.y2} L ${gutter - 5} ${one.y2 + 3.5}`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                />
              </g>
            )
          })}
        </svg>
      )}
      {children}
    </div>
  )
}
