import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'

import { api, type Picked } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel, Stat, Stats } from '@/components/Panel'
import { TechniqueCards } from '@/components/TechniqueCards'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { lastAt, share } from '@/lib/format'

// the problem a user picked, before its statement is served. The path names
// the problem, and `?technique=` or `?card=` names the page the pick came from
export function ProblemPage() {
  const { problemId = '' } = useParams()
  const [search] = useSearchParams()
  const technique = search.get('technique')
  const slug = search.get('card')
  // the listing is the third page a pick comes from, beside a technique and a
  // card, and it names no record of its own
  const listing = search.get('from') === 'problems'
  const navigate = useNavigate()
  // read only where the pick came from a card: the page names the card it
  // returns to, and the claim answers for that card's technique
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
  const [starting, setStarting] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)

  // the clock starts on this press, so a card read before it stays off the
  // clock. A sitting already running on the problem is reached, not restarted
  async function start() {
    setStarting(true)
    setRefused(null)
    try {
      const { data, error } = await api.POST('/api/problems/{problem_id}/sittings', {
        params: { path: { problem_id: problemId } },
      })
      if (data)
        navigate(
          sittingPath(data.sitting.id, {
            technique: card.data?.card.technique ?? technique,
            card: slug,
          }),
        )
      else setRefused(described(error))
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setStarting(false)
    }
  }

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
        {(picked) => (
          <div className="space-y-section">
            {/* the one act this page asks for, beside what the user has done
                on this problem before */}
            <Panel>
              <Stats>
                {standing(picked).map((stat) => (
                  <Stat key={stat.label} value={stat.value} label={stat.label} />
                ))}
                {!picked.retired && (
                  <Button className="ml-auto" onClick={start} disabled={starting}>
                    {starting ? 'Starting…' : 'Start the sitting'}
                  </Button>
                )}
              </Stats>
              <p className="text-meta text-muted-foreground">
                {picked.retired
                  ? 'This problem was retired: its statement asked for something its cases do not decide. It is served to nobody, and the attempts above stay in your log.'
                  : 'No statement on this page. It is served on that press, and the clock starts with it.'}
              </p>
              {refused && (
                <p className="text-meta text-destructive">The sitting did not start: {refused}</p>
              )}
            </Panel>

            {/* the technique the pick came from, the card's own where it came
                from a card, and the problem's where it came from neither */}
            <section className="space-y-stack">
              <h2 className="text-heading font-medium">Before you start</h2>
              <p className="text-meta text-muted-foreground">
                The card teaches the form this problem is written for. Reading it is off the
                clock, and no sitting requires it.
              </p>
              {cards(picked, technique, card.data?.card.technique ?? null).map((one) => (
                <TechniqueCards key={one} technique={one} />
              ))}
            </section>
          </div>
        )}
      </Loaded>
    </section>
  )
}

// the sitting carries both on: the claim answers for the technique, and the
// sitting returns to the card it came from
function sittingPath(
  sittingId: string,
  from: { technique: string | null; card: string | null },
): string {
  const query = new URLSearchParams()
  if (from.technique !== null) query.set('technique', from.technique)
  if (from.card !== null) query.set('card', from.card)
  const asked = query.toString()
  return `/sittings/${encodeURIComponent(sittingId)}${asked ? `?${asked}` : ''}`
}

// the techniques whose cards are offered beside the problem
function cards(picked: Picked, technique: string | null, carded: string | null): string[] {
  if (carded !== null) return [carded]
  return technique === null ? picked.techniques : [technique]
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
