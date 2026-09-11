import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { api, type Board, type TechniqueRow } from '@/api/client'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function BoardPage() {
  const [board, setBoard] = useState<Board | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    api
      .GET('/api/board', { signal: controller.signal })
      .then(({ data, error }) => {
        if (data) setBoard(data)
        else setError(JSON.stringify(error))
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(String(reason))
      })
    return () => controller.abort()
  }, [])

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
                <TableCell className="text-right tabular-nums">{solved(row)}</TableCell>
                <TableCell>{practised(row.last_attempt_at)}</TableCell>
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

function solved(row: TechniqueRow): string {
  return row.attempt_count === 0 ? '—' : `${row.solved_count}/${row.attempt_count}`
}

function practised(at: string | null | undefined): string {
  if (!at) return 'never'
  const days = Math.max(0, Math.floor((Date.now() - new Date(at).getTime()) / 86_400_000))
  return `${new Date(at).toLocaleDateString()} (${days}d ago)`
}
