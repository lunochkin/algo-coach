import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { api, type Candidate, candidates } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { TechniqueCards } from '@/components/TechniqueCards'
import { Button } from '@/components/ui/button'
import { lastAt, share } from '@/lib/format'

// the problem a user picked, before its statement is served
export function ProblemPage() {
  const { technique = '', problemId = '' } = useParams()
  const navigate = useNavigate()
  const rows = useLoaded((signal) => candidates(technique, signal), `candidates:${technique}`)
  const [starting, setStarting] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  const picked = rows.data?.find((row) => row.problem_id === problemId)

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
          `/sittings/${encodeURIComponent(data.sitting.id)}?technique=${encodeURIComponent(technique)}`,
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
        back={{ to: `/techniques/${encodeURIComponent(technique)}`, label: technique }}
        title={picked?.title ?? 'The problem'}
        note={picked && standing(picked)}
      />
      <Loaded
        of="the problem"
        state={rows}
        blank={`This problem is not a candidate for ${technique}.`}
        blankWhen={(rows) => !rows.some((row) => row.problem_id === problemId)}
      >
        {() => (
          <div className="space-y-stack">
            <TechniqueCards technique={technique} />
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

// what the user has done on this problem, as the candidates list reports it
function standing(picked: Candidate): string {
  return [
    picked.difficulty ?? 'no difficulty',
    `${picked.attempt_count} attempt(s), ${share(picked.solved_count, picked.attempt_count)} solved`,
    `last ${lastAt(picked.last_attempt_at)}`,
  ].join(' · ')
}
