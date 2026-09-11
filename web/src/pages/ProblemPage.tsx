import { Link, useParams } from 'react-router'

import { candidates } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Button } from '@/components/ui/button'

// the problem a user picked, before its statement is served
export function ProblemPage() {
  const { technique = '', problemId = '' } = useParams()
  const { data: rows, error } = useLoaded(
    (signal) => candidates(technique, signal),
    `candidates:${technique}`,
  )
  const picked = rows?.find((row) => row.problem_id === problemId)

  return (
    <section className="space-y-4">
      <Button variant="outline" asChild>
        <Link to={`/techniques/${encodeURIComponent(technique)}`}>Back to the candidates</Link>
      </Button>
      {error ? (
        <p className="text-destructive">The problem did not load: {error}</p>
      ) : !rows ? (
        <p className="text-muted-foreground">Loading the problem…</p>
      ) : !picked ? (
        <p className="text-muted-foreground">This problem is not a candidate for {technique}.</p>
      ) : (
        <h1 className="text-2xl font-semibold">{picked.title}</h1>
      )}
    </section>
  )
}
