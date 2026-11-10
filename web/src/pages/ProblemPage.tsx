import { lazy } from 'react'
import { useParams, useSearchParams } from 'react-router'

import { api, type Picked } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel, Stat, Stats } from '@/components/Panel'
import { Badge } from '@/components/ui/badge'
import { lastAt, share } from '@/lib/format'

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
    <section className="space-y-section">
      <PageHeader
        back={
          slug !== null
            ? {
                to: `/cards/${encodeURIComponent(slug)}`,
                label: card.data?.card.title ?? slug,
              }
            : listing
              ? { to: '/problems', label: 'Problems' }
              : technique === null
                ? { to: '/', label: 'Board' }
                : { to: `/techniques/${encodeURIComponent(technique)}`, label: technique }
        }
        title={picked.data?.title ?? 'The problem'}
        note={
          picked.data && (
            <span className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="font-normal">
                {picked.data.difficulty ?? 'no difficulty'}
              </Badge>
              <span>{picked.data.techniques.join(' · ')}</span>
            </span>
          )
        }
      />
      <Loaded of="the problem" state={picked}>
        {(picked) =>
          picked.retired ? (
            <Panel>
              <Stats>
                {standing(picked).map((stat) => (
                  <Stat key={stat.label} value={stat.value} label={stat.label} />
                ))}
              </Stats>
              <p className="text-meta text-muted-foreground">
                This problem was retired: its statement asked for something its cases do not
                decide. It is served to nobody, and the attempts above stay in your log.
              </p>
            </Panel>
          ) : (
            <p className="text-meta text-muted-foreground">Opening the problem…</p>
          )
        }
      </Loaded>
    </section>
  )
}

// what the user has done on this problem, as counts rather than a sentence
function standing(picked: Picked): { value: string | number; label: string }[] {
  if (picked.attempt_count === 0) return [{ value: 'never', label: 'attempted' }]
  return [
    { value: picked.attempt_count, label: picked.attempt_count === 1 ? 'attempt' : 'attempts' },
    { value: share(picked.solved_count, picked.attempt_count), label: 'solved' },
    { value: lastAt(picked.last_attempt_at), label: 'last attempted' },
  ]
}
