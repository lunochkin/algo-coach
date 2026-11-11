import type { ReactNode } from 'react'

import {
  moduleStats,
  PAUSED,
  QUESTIONS_PASSED,
  type ModuleRow as Row,
  moduleRowNote,
} from '@algo-coach/core'

import { PickRow } from '@/components/PickRow'
import { Tag } from '@/components/Tag'
import { modulePath } from '@/knowledge/paths'

// one module reads as one row wherever it is listed, the knowledge home and
// the board alike: `pages.md`, A page's areas. `from` names the page the
// module's way back returns to
export function ModuleRow({ row, from, aside }: { row: Row; from?: 'board'; aside?: ReactNode }) {
  return (
    <PickRow
      to={modulePath(row.c.slug, from)}
      title={row.c.title}
      badge={row.c.paused && <Tag>{PAUSED}</Tag>}
      note={moduleRowNote(row)}
      stats={moduleStats(row.toReview, row.total)}
      progress={{ value: row.passed, total: row.total, label: QUESTIONS_PASSED }}
      aside={aside}
    />
  )
}
