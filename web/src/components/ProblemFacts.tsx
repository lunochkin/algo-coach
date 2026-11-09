import { Link } from 'react-router'

import { api, type ListedCard, type Picked } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Badge } from '@/components/ui/badge'
import { lastAt, share } from '@/lib/format'

// what the picked problem's page carried, in one line above the statement:
// the level, the techniques, what the user has done on it, and the cards.
// `technique` narrows the cards to the one the pick came from
export function ProblemFacts({
  problemId,
  technique,
}: {
  problemId: string
  technique: string | null
}) {
  const picked = useLoaded(
    (signal) =>
      api.GET('/api/problems/{problem_id}', {
        params: { path: { problem_id: problemId } },
        signal,
      }),
    `problem:${problemId}`,
  )
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')

  // a fact line is beside the sitting, never in its way: a failed read shows
  // nothing rather than a refusal over the statement
  const problem = picked.data
  if (!problem) return null
  const asked = technique === null ? problem.techniques : [technique]
  const offered = (cards.data ?? []).filter((card) => taught(card, asked))

  return (
    // spaced rather than dotted, as a row's counts are: a separator of its own
    // would start a line wherever the line wraps
    <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-meta text-muted-foreground">
      {problem.difficulty && (
        <Badge variant="outline" className="font-normal">
          {problem.difficulty}
        </Badge>
      )}
      <span>{problem.techniques.join(' · ')}</span>
      <span>{tried(problem)}</span>
      {offered.length > 0 && (
        <span>
          {offered.length === 1 ? 'Card' : 'Cards'}:{' '}
          {offered.map((card, index) => (
            <span key={card.slug}>
              {index > 0 && ', '}
              <Link
                to={`/cards/${encodeURIComponent(card.slug)}`}
                className="font-medium text-foreground underline-offset-4 hover:underline"
              >
                {card.title}
              </Link>
            </span>
          ))}
        </span>
      )}
    </p>
  )
}

// a card on a narrower technique teaches its family too, as the cards list
// groups it
function taught(card: ListedCard, techniques: string[]): boolean {
  return techniques.includes(card.technique) || techniques.includes(card.family)
}

function tried(picked: Picked): string {
  if (picked.attempt_count === 0) return 'never attempted'
  const attempts = picked.attempt_count === 1 ? '1 attempt' : `${picked.attempt_count} attempts`
  return `${attempts}, ${share(picked.solved_count, picked.attempt_count)} solved, last ${lastAt(picked.last_attempt_at)}`
}
