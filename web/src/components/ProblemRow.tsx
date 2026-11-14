import { techniquesLine } from '@climb/core'

import type { Candidate, Listed } from '@/api/client'
import { PickRow } from '@/components/PickRow'
import { Tag } from '@/components/Tag'
import { counts } from '@/lib/format'

// one problem as a row, wherever a list offers it: the techniques read under
// the title, where a row's right-hand cluster is the counts. `query` names the
// page the pick came from, which the problem's way back returns to
export function ProblemRow({
  problem,
  query,
}: {
  problem: Listed | Candidate
  query: URLSearchParams
}) {
  return (
    <PickRow
      to={`/problems/${encodeURIComponent(problem.problem_id)}?${query.toString()}`}
      title={problem.title}
      badge={problem.difficulty && <Tag>{problem.difficulty}</Tag>}
      stats={counts(problem)}
      note={techniquesLine(problem.techniques)}
      mono
    />
  )
}
