import { Link } from 'react-router'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
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
  const board = useLoaded((signal) => api.GET('/api/board', { signal }), 'board')

  return (
    <section className="space-y-section">
      <PageHeader title="Pick a technique" />
      <Loaded
        of="the board"
        state={board}
        blank="No served problem carries a technique yet."
        blankWhen={(one) => one.rows.length === 0}
      >
        {(board) => (
          <div className="space-y-stack">
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
            {/* the attempts no row holds, on one line under the table */}
            {(board.ungrouped > 0 || board.excluded > 0) && (
              <p className="text-meta text-muted-foreground">
                {[
                  board.ungrouped > 0 && `${board.ungrouped} attempt(s) grouped nowhere`,
                  board.excluded > 0 && `${board.excluded} on a defective problem`,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            )}
          </div>
        )}
      </Loaded>
    </section>
  )
}
