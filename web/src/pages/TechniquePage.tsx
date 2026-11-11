import { useParams } from 'react-router'

import {
  techniqueCards,
  BACK_BOARD,
  TECHNIQUE_CARDS,
  OF,
  TECHNIQUE_NONE,
  TECHNIQUE_PROBLEMS,
} from '@algo-coach/core'

import { api, candidates } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickPanel } from '@/components/PickRow'
import { ProblemRow } from '@/components/ProblemRow'
import { SectionHeading } from '@/components/SectionHeading'

export function TechniquePage() {
  const { technique = '' } = useParams()
  const rows = useLoaded((signal) => candidates(technique, signal), `candidates:${technique}`)
  // the technique's cards, read as the cards list reads them: a card is offered,
  // and no sitting requires one
  const taught = useLoaded(
    (signal) =>
      api.GET('/api/techniques/{technique}/cards', { params: { path: { technique } }, signal }),
    `technique-cards:${technique}`,
  )
  const listed = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')
  const cards = techniqueCards(listed.data ?? [], taught.data ?? [])

  return (
    <section className="space-y-section">
      <PageHeader back={{ to: '/', label: BACK_BOARD }} title={technique} />
      {cards.length > 0 && (
        <section className="space-y-stack">
          <SectionHeading title={TECHNIQUE_CARDS} count={cards.length} />
          <CardPanel technique={null} cards={cards} />
        </section>
      )}
      <Loaded of={OF.technique} state={rows} blank={TECHNIQUE_NONE}>
        {(rows) => (
          <div className="space-y-stack">
            {/* no statement in the list: the clock starts when it is served */}
            <SectionHeading title={TECHNIQUE_PROBLEMS} count={rows.length} />
            <PickPanel>
              {rows.map((row) => (
                <ProblemRow
                  key={row.problem_id}
                  problem={row}
                  query={new URLSearchParams({ technique })}
                />
              ))}
            </PickPanel>
          </div>
        )}
      </Loaded>
    </section>
  )
}
