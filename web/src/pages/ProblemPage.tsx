import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { api, candidates } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { TechniqueCards } from '@/components/TechniqueCards'
import { Button } from '@/components/ui/button'

// the problem a user picked, before its statement is served
export function ProblemPage() {
  const { technique = '', problemId = '' } = useParams()
  const navigate = useNavigate()
  const rows = useLoaded((signal) => candidates(technique, signal), `candidates:${technique}`)
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
    <section className="space-y-4">
      <Button variant="outline" asChild>
        <Link to={`/techniques/${encodeURIComponent(technique)}`}>Back to the candidates</Link>
      </Button>
      <Loaded
        of="the problem"
        state={rows}
        blank={`This problem is not a candidate for ${technique}.`}
        blankWhen={(rows) => !rows.some((row) => row.problem_id === problemId)}
      >
        {(rows) => {
          const picked = rows.find((row) => row.problem_id === problemId)
          return (
            <div className="space-y-4">
              <h1 className="text-2xl font-semibold">{picked?.title}</h1>
              <TechniqueCards technique={technique} />
              <Button onClick={start} disabled={starting}>
                {starting ? 'Starting…' : 'Start the sitting'}
              </Button>
              {refused && <p className="text-destructive">The sitting did not start: {refused}</p>}
            </div>
          )
        }}
      </Loaded>
    </section>
  )
}
