import { Link } from 'react-router'

import { api, type TechniqueRow } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickList, PickRow } from '@/components/PickRow'
import { counts } from '@/lib/format'

export function BoardPage() {
  const board = useLoaded((signal) => api.GET('/api/board', { signal }), 'board')

  return (
    <section className="space-y-section">
      <PageHeader
        title="Pick a technique"
        note="Every technique a served problem carries, stalest first."
      />
      <Loaded
        of="the board"
        state={board}
        blank="No served problem carries a technique yet."
        blankWhen={(one) => one.rows.length === 0}
      >
        {(board) => {
          // a technique never practised ranks stalest, so the untouched ones
          // come first. As names alone they stay one glance rather than thirty
          // rows of zeros
          const untouched = board.rows.filter((row) => row.attempt_count === 0)
          const practised = board.rows.filter((row) => row.attempt_count > 0)

          return (
            <div className="space-y-section">
              {untouched.length > 0 && (
                <section className="space-y-stack">
                  <Heading count={untouched.length}>Not practised yet</Heading>
                  {/* names rather than chips: a bordered chip is what the
                      listing's filters are, and these open a technique */}
                  <div className="flex flex-wrap gap-x-5 gap-y-1">
                    {untouched.map((row) => (
                      <Link
                        key={row.technique}
                        to={`/techniques/${encodeURIComponent(row.technique)}`}
                        className="underline-offset-4 hover:underline"
                      >
                        {row.technique}
                      </Link>
                    ))}
                  </div>
                </section>
              )}

              {practised.length > 0 && (
                <section className="space-y-stack">
                  <Heading count={practised.length}>Practised</Heading>
                  <PickList>
                    {practised.map((row) => (
                      <Practised key={row.technique} row={row} />
                    ))}
                  </PickList>
                </section>
              )}

              {/* the attempts no row holds, on one line under the lists */}
              {(board.ungrouped > 0 || board.excluded > 0) && (
                <p className="text-meta text-muted-foreground">
                  {[
                    board.ungrouped > 0 && `${board.ungrouped} attempt(s) grouped nowhere`,
                    board.excluded > 0 && `${board.excluded} on a defective problem`,
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              )}
            </div>
          )
        }}
      </Loaded>
    </section>
  )
}

function Practised({ row }: { row: TechniqueRow }) {
  return (
    <PickRow
      to={`/techniques/${encodeURIComponent(row.technique)}`}
      title={row.technique}
      stats={counts(row)}
    />
  )
}

function Heading({ count, children }: { count: number; children: string }) {
  return (
    <h2 className="flex items-baseline gap-2 text-heading font-medium">
      {children}
      <span className="text-meta font-normal text-muted-foreground tabular-nums">{count}</span>
    </h2>
  )
}
