import { Link } from 'react-router'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
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

export function BoardPage() {
  const { data: board, error } = useLoaded(
    (signal) => api.GET('/api/board', { signal }),
    'board',
  )

  if (error) return <p className="text-destructive">The board did not load: {error}</p>
  if (!board) return <p className="text-muted-foreground">Loading the board…</p>

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Pick a technique</h1>
      {board.rows.length === 0 ? (
        <p className="text-muted-foreground">No served problem carries a technique yet.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Technique</TableHead>
              <TableHead className="text-right">Attempts</TableHead>
              <TableHead className="text-right">Solved</TableHead>
              <TableHead>Last practised</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {board.rows.map((row) => (
              <TableRow key={row.technique}>
                <TableCell>
                  <Button variant="link" className="px-0" asChild>
                    <Link to={`/techniques/${encodeURIComponent(row.technique)}`}>
                      {row.technique}
                    </Link>
                  </Button>
                </TableCell>
                <TableCell className="text-right tabular-nums">{row.attempt_count}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {share(row.solved_count, row.attempt_count)}
                </TableCell>
                <TableCell>{lastAt(row.last_attempt_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {board.ungrouped > 0 && (
        <p className="text-sm text-muted-foreground">
          {board.ungrouped} attempt(s) grouped nowhere: no technique resolved
        </p>
      )}
      {board.excluded > 0 && (
        <p className="text-sm text-muted-foreground">
          {board.excluded} attempt(s) on a defective problem, not counted
        </p>
      )}
    </section>
  )
}
