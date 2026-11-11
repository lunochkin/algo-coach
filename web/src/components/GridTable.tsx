import type { ReactNode } from 'react'

import { GRID_LEVEL_HEAD } from '@/lib/grid'
import { cn } from '@/lib/utils'

// a grid read by level, the module's groups and the certifications: one edge,
// one head row and one body, so a level reads in the same place on both
export function GridTable(props: {
  first: string
  levels: { key: string | number; head: ReactNode; faint?: boolean }[]
  children: ReactNode
}) {
  return (
    <div className="overflow-x-auto rounded-xl border bg-card">
      <table className="w-full text-meta">
        <thead>
          <tr className="text-meta text-muted-foreground">
            <th className="px-4 py-2 text-left font-normal">{props.first}</th>
            {props.levels.map((l) => (
              <th key={l.key} className={cn(GRID_LEVEL_HEAD, l.faint && 'opacity-60')}>
                {l.head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">{props.children}</tbody>
      </table>
    </div>
  )
}
