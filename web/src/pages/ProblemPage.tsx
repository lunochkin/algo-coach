import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'

import { api, type Picked } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { TechniqueCards } from '@/components/TechniqueCards'
import { Button } from '@/components/ui/button'
import { lastAt, share } from '@/lib/format'

// the problem a user picked, before its statement is served. The path names
// the problem, and `?technique=` or `?card=` names the page the pick came from
export function ProblemPage() {
  const { problemId = '' } = useParams()
  const [search] = useSearchParams()
  const technique = search.get('technique')
  const slug = search.get('card')
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
            : technique === null
              ? { to: '/', label: 'Board' }
              : { to: `/techniques/${encodeURIComponent(technique)}`, label: technique }
        }
        title={picked.data?.title ?? 'The problem'}
        note={picked.data && standing(picked.data)}
      />
      <Loaded of="the problem" state={picked}>
        {(picked) => (
          <div className="space-y-stack">
            {/* the technique the pick came from, the card's own where it came
                from a card, and the problem's where it came from neither */}
            {cards(picked, technique, card.data?.card.technique ?? null).map((one) => (
              <TechniqueCards key={one} technique={one} />
            ))}
            {/* the one act this page asks for */}
            <div>
              <Button onClick={start} disabled={starting}>
                {starting ? 'Starting…' : 'Start the sitting'}
              </Button>
            </div>
            <p className="text-meta text-muted-foreground">
              The statement is served on that press, and the clock starts with it.
            </p>
            {refused && <p className="text-destructive">The sitting did not start: {refused}</p>}
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

// what the user has done on this problem
function standing(picked: Picked): string {
  return [
    picked.difficulty ?? 'no difficulty',
    `${picked.attempt_count} attempt(s), ${share(picked.solved_count, picked.attempt_count)} solved`,
    `last ${lastAt(picked.last_attempt_at)}`,
  ].join(' · ')
}
