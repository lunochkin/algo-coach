import type { ReactNode } from 'react'
import {
  boardView,
  inProgress,
  BOARD_TITLE,
  BOARD_NOTE,
  OF,
  BOARD_NONE,
  BOARD_STUDYING,
  BOARD_UNTOUCHED,
  BOARD_PRACTISED,
} from '@algo-coach/core'
import { Link } from 'react-router'

import { api, type TechniqueRow } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickList, PickRow } from '@/components/PickRow'
import { SectionHeading } from '@/components/SectionHeading'
import { counts } from '@/lib/format'

export function BoardPage() {
  const board = useLoaded((signal) => api.GET('/api/board', { signal }), 'board')
  // the cards in progress read as the cards list draws them, so one card reads
  // one way on both pages
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')
  const studying = inProgress(cards.data ?? [])

  return (
    <section className="space-y-section">
      <PageHeader title={BOARD_TITLE} note={BOARD_NOTE} />
      <Loaded
        of={OF.board}
        state={board}
        blank={BOARD_NONE}
        blankWhen={(one) => one.rows.length === 0}
      >
        {(board) => {
          // a technique never practised ranks stalest, so the untouched ones
          // come first. As names alone they stay one glance rather than thirty
          // rows of zeros
          const { untouched, practised, foot } = boardView(board)

          return (
            <div className="space-y-section">
              {/* the study the user declared, ahead of any staleness ranking */}
              {studying.length > 0 && (
                <section className="space-y-stack">
                  <SectionHeading title={BOARD_STUDYING} count={studying.length} />
                  <CardPanel technique={null} cards={studying} />
                </section>
              )}

              {untouched.length > 0 && (
                <Group title={BOARD_UNTOUCHED} count={untouched.length}>
                  {/* names rather than chips: a bordered chip is what the
                      listing's filters are, and these open a technique */}
                  <div className="flex flex-wrap gap-x-5 gap-y-1 px-4 py-3">
                    {untouched.map((row) => (
                      <Link
                        key={row.technique}
                        to={`/techniques/${encodeURIComponent(row.technique)}`}
                        className="font-medium underline-offset-4 hover:underline"
                      >
                        {row.technique}
                      </Link>
                    ))}
                  </div>
                </Group>
              )}

              {practised.length > 0 && (
                <Group title={BOARD_PRACTISED} count={practised.length}>
                  <PickList>
                    {practised.map((row) => (
                      <Practised key={row.technique} row={row} />
                    ))}
                  </PickList>
                </Group>
              )}

              {/* the attempts no row holds, on one line under the lists */}
              {foot && <p className="text-meta text-muted-foreground">{foot}</p>}
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

// a section heading above a bordered panel, as the cards list draws its
// sections. A panel's own header strip is kept for naming a record
function Group({ title, count, children }: { title: string; count: number; children: ReactNode }) {
  return (
    <section className="space-y-stack">
      <SectionHeading title={title} count={count} />
      <div className="overflow-hidden rounded-xl border bg-card">{children}</div>
    </section>
  )
}
