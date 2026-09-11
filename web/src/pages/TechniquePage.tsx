import { Link, useParams } from 'react-router'

import { candidates } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { TechniqueCards } from '@/components/TechniqueCards'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { lastAt, share } from '@/lib/format'

export function TechniquePage() {
  const { technique = '' } = useParams()
  const { data: rows, error } = useLoaded(
    (signal) => candidates(technique, signal),
    `candidates:${technique}`,
  )

  return (
    <section className="space-y-4">
      <Button variant="outline" asChild>
        <Link to="/">Back to the board</Link>
      </Button>
      <h1 className="text-2xl font-semibold">{technique}</h1>
      <TechniqueCards technique={technique} />
      {error ? (
        <p className="text-destructive">The candidates did not load: {error}</p>
      ) : !rows ? (
        <p className="text-muted-foreground">Loading the candidates…</p>
      ) : rows.length === 0 ? (
        <p className="text-muted-foreground">No served problem carries this technique.</p>
      ) : (
        <>
          {/* no statement in the list: the clock starts when it is served */}
          <h2 className="text-lg font-medium">Pick a problem</h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Problem</TableHead>
                <TableHead>Difficulty</TableHead>
                <TableHead className="text-right">Attempts</TableHead>
                <TableHead className="text-right">Solved</TableHead>
                <TableHead>Last attempted</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.problem_id}>
                  <TableCell>
                    <Button variant="link" className="px-0" asChild>
                      <Link to={`problems/${encodeURIComponent(row.problem_id)}`}>{row.title}</Link>
                    </Button>
                  </TableCell>
                  <TableCell>{row.difficulty ?? '—'}</TableCell>
                  <TableCell className="text-right tabular-nums">{row.attempt_count}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {share(row.solved_count, row.attempt_count)}
                  </TableCell>
                  <TableCell>{lastAt(row.last_attempt_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}
    </section>
  )
}
