import {
  BACK_PROBLEMS,
  BACK_BOARD,
  PROBLEM_FALLBACK,
  NO_DIFFICULTY,
  OF,
  techniqueStats,
  PROBLEM_RETIRED,
  PROBLEM_OPENING,
  techniquesLine,
} from '@algo-coach/core'
import { lazy, useState } from 'react'
import { useParams, useSearchParams } from 'react-router'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel, Stat, Stats } from '@/components/Panel'
import { Badge } from '@/components/ui/badge'

// the editor is the bulk of the bundle, and a retired problem needs none
const SittingView = lazy(() =>
  import('@/components/SittingView').then((m) => ({ default: m.SittingView })),
)

// opening a problem serves its statement and mints nothing, so no press
// stands between the pick and the statement. A retired problem serves
// nothing and reads as its record. `?technique=` or `?card=` names the page
// the pick came from
export function ProblemPage() {
  const { problemId = '' } = useParams()
  // the moment the page opened, which the retired record's counts are read at
  const [now] = useState(() => Date.now())
  const [search] = useSearchParams()
  const technique = search.get('technique')
  const slug = search.get('card')
  // the listing is the third page a pick comes from, beside a technique and a
  // card, and it names no record of its own
  const listing = search.get('from') === 'problems'
  // read only where the pick came from a card: the sitting returns to it, and
  // the claim answers for that card's technique
  const card = useLoaded(
    (signal) =>
      slug === null
        ? Promise.resolve({ data: null })
        : api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    slug === null ? 'no-card' : `card:${slug}`,
  )
  const picked = useLoaded(
    (signal) =>
      api.GET('/api/problems/{problem_id}', {
        params: { path: { problem_id: problemId } },
        signal,
      }),
    `problem:${problemId}`,
  )

  const served = picked.data !== undefined && !picked.data.retired
  const carded = slug === null || card.data !== undefined
  // the claim answers for the card's own technique where a card offered it
  if (served && carded)
    return (
      <SittingView
        problemId={problemId}
        drilled={card.data?.card.technique ?? technique}
        card={slug}
      />
    )

  return (
    // the layout is wide on this path, which holds the sitting; the record and
    // the loading header read in the reading column every other page reads in
    <section className="mx-auto max-w-reading space-y-section">
      <PageHeader
        back={
          slug !== null
            ? {
                to: `/cards/${encodeURIComponent(slug)}`,
                label: card.data?.card.title ?? slug,
              }
            : listing
              ? { to: '/problems', label: BACK_PROBLEMS }
              : technique === null
                ? { to: '/', label: BACK_BOARD }
                : { to: `/techniques/${encodeURIComponent(technique)}`, label: technique }
        }
        title={picked.data?.title ?? PROBLEM_FALLBACK}
        note={
          picked.data && (
            <span className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="font-normal">
                {picked.data.difficulty ?? NO_DIFFICULTY}
              </Badge>
              <span>{techniquesLine(picked.data.techniques)}</span>
            </span>
          )
        }
      />
      <Loaded of={OF.problem} state={picked}>
        {(picked) =>
          picked.retired ? (
            <Panel>
              <Stats>
                {techniqueStats(picked, now).map((stat) => (
                  <Stat key={stat.label} value={stat.value} label={stat.label} />
                ))}
              </Stats>
              <p className="text-meta text-muted-foreground">{PROBLEM_RETIRED}</p>
            </Panel>
          ) : (
            <p className="text-meta text-muted-foreground">{PROBLEM_OPENING}</p>
          )
        }
      </Loaded>
    </section>
  )
}
