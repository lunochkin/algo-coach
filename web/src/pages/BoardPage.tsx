import { useMemo } from 'react'

import {
  boardView,
  inProgress,
  BOARD_TITLE,
  BOARD_NOTE,
  OF,
  BOARD_NONE,
  BOARD_STUDYING,
  BOARD_NEXT,
  JUDGE_NOTE,
  JUDGE_TITLE,
  boardMoreCards,
  nextCards,
  BOARD_UNTOUCHED,
  BOARD_PRACTISED,
  MODULES_HEADING,
  orderedModuleRows,
} from '@algo-coach/core'
import { Link } from 'react-router'

import { api, type TechniqueRow } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PageSection } from '@/components/PageSection'
import { PickList, PickPanel, PickRow } from '@/components/PickRow'
import { SectionHeading } from '@/components/SectionHeading'
import { useLearner } from '@/knowledge/learner'
import { KnowledgeNext } from '@/knowledge/KnowledgeNext'
import { ModuleRow } from '@/knowledge/ModuleRow'
import { counts } from '@/lib/format'

export function BoardPage() {
  const board = useLoaded((signal) => api.GET('/api/board', { signal }), 'board')
  // the cards in progress read as the cards list draws them, so one card reads
  // one way on both pages
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')
  const studying = inProgress(cards.data ?? [])
  const next = nextCards(cards.data ?? [])
  const { catalog, board: learnerBoard, order, now } = useLearner()
  const modules = useMemo(() => {
    const all = learnerBoard(null)
    return catalog && all ? orderedModuleRows(all, order, now) : []
  }, [catalog, learnerBoard, order, now])

  return (
    <section className="space-y-section">
      <PageHeader title={BOARD_TITLE} note={BOARD_NOTE} />
      {/* the knowledge study first, from the device's copy, so it reads before
          and without the engine's answer: `pages.md`, Sections */}
      <KnowledgeNext controls={false} />
      {modules.length > 0 && (
        <section className="space-y-stack">
          <SectionHeading title={MODULES_HEADING} count={modules.length} />
          <PickPanel>
            {modules.map((row) => (
              <ModuleRow key={row.c.slug} row={row} from="board" />
            ))}
          </PickPanel>
        </section>
      )}
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

              {/* what the card graph opens next, the shallowest first */}
              {/* the short exercise, across every card: `pages.md`, Judging */}
              <Link
                to="/judge"
                className="block rounded-xl border bg-card px-4 py-3 hover:bg-accent"
              >
                <span className="font-medium">{JUDGE_TITLE}</span>
                <span className="mt-1 block text-meta text-muted-foreground">{JUDGE_NOTE}</span>
              </Link>

              {next.cards.length > 0 && (
                <section className="space-y-stack">
                  <SectionHeading title={BOARD_NEXT} count={next.cards.length + next.more} />
                  <CardPanel technique={null} cards={next.cards} />
                  {next.more > 0 && (
                    <Link
                      to="/cards"
                      className="text-meta text-muted-foreground underline-offset-4 hover:underline"
                    >
                      {boardMoreCards(next.more)}
                    </Link>
                  )}
                </section>
              )}

              {untouched.length > 0 && (
                <PageSection
                  id="untouched"
                  title={BOARD_UNTOUCHED}
                  count={untouched.length}
                  body="rows"
                >
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
                </PageSection>
              )}

              {practised.length > 0 && (
                <PageSection
                  id="practised"
                  title={BOARD_PRACTISED}
                  count={practised.length}
                  body="rows"
                >
                  <PickList>
                    {practised.map((row) => (
                      <Practised key={row.technique} row={row} />
                    ))}
                  </PickList>
                </PageSection>
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
