import { useParams } from 'react-router'

import { candidates } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickList, PickRow } from '@/components/PickRow'
import { counts } from '@/lib/format'
import { TechniqueCards } from '@/components/TechniqueCards'
import { Badge } from '@/components/ui/badge'

export function TechniquePage() {
  const { technique = '' } = useParams()
  const rows = useLoaded((signal) => candidates(technique, signal), `candidates:${technique}`)

  return (
    <section className="space-y-section">
      <PageHeader
        back={{ to: '/', label: 'Board' }}
        title={technique}
        note={<TechniqueCards technique={technique} />}
      />
      <Loaded of="the candidates" state={rows} blank="No served problem carries this technique.">
        {(rows) => (
          <div className="space-y-stack">
            {/* no statement in the list: the clock starts when it is served */}
            <h2 className="flex items-baseline gap-2 text-heading font-medium">
              Pick a problem
              <span className="text-meta font-normal text-muted-foreground tabular-nums">
                {rows.length}
              </span>
            </h2>
            <PickList>
              {rows.map((row) => (
                <PickRow
                  key={row.problem_id}
                  to={`/problems/${encodeURIComponent(row.problem_id)}?technique=${encodeURIComponent(technique)}`}
                  title={row.title}
                  badge={
                    row.difficulty && (
                      <Badge variant="outline" className="font-normal">
                        {row.difficulty}
                      </Badge>
                    )
                  }
                  stats={counts(row)}
                />
              ))}
            </PickList>
          </div>
        )}
      </Loaded>
    </section>
  )
}
