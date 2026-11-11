import { useParams } from 'react-router'

import { techniqueCards } from '@algo-coach/core'

import { api, candidates } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickPanel, PickRow } from '@/components/PickRow'
import { SectionHeading } from '@/components/SectionHeading'
import { counts } from '@/lib/format'
import { Badge } from '@/components/ui/badge'

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
      <PageHeader back={{ to: '/', label: 'Board' }} title={technique} />
      {cards.length > 0 && (
        <section className="space-y-stack">
          <SectionHeading title="Cards" count={cards.length} />
          <CardPanel technique={null} cards={cards} />
        </section>
      )}
      <Loaded of="the candidates" state={rows} blank="No served problem carries this technique.">
        {(rows) => (
          <div className="space-y-stack">
            {/* no statement in the list: the clock starts when it is served */}
            <SectionHeading title="Problems" count={rows.length} />
            <PickPanel>
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
            </PickPanel>
          </div>
        )}
      </Loaded>
    </section>
  )
}
