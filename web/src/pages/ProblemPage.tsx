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
// the problem, and `?technique=` names the page the pick came from
export function ProblemPage() {
  const { problemId = '' } = useParams()
  const [search] = useSearchParams()
  const technique = search.get('technique')
  const navigate = useNavigate()
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
      if (data) navigate(sittingPath(data.sitting.id, technique))
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
          technique === null
            ? { to: '/', label: 'Board' }
            : { to: `/techniques/${encodeURIComponent(technique)}`, label: technique }
        }
        title={picked.data?.title ?? 'The problem'}
        note={picked.data && standing(picked.data)}
      />
      <Loaded of="the problem" state={picked}>
        {(picked) => (
          <div className="space-y-stack">
            {/* the cards of the technique the pick came from, and of the
                problem's own techniques where it came from nowhere */}
            {(technique === null ? picked.techniques : [technique]).map((one) => (
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

// the sitting carries the technique on, as the claim answers for it
function sittingPath(sittingId: string, technique: string | null): string {
  const path = `/sittings/${encodeURIComponent(sittingId)}`
  return technique === null ? path : `${path}?technique=${encodeURIComponent(technique)}`
}

// what the user has done on this problem
function standing(picked: Picked): string {
  return [
    picked.difficulty ?? 'no difficulty',
    `${picked.attempt_count} attempt(s), ${share(picked.solved_count, picked.attempt_count)} solved`,
    `last ${lastAt(picked.last_attempt_at)}`,
  ].join(' · ')
}
