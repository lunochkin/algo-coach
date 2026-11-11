import { Link } from 'react-router'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Badge } from '@/components/ui/badge'
import { problemFacts } from '@/lib/format'

// what the picked problem's page carried, in one line above the statement:
// the difficulty, the techniques, what the user has done on it, and the cards.
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
  const facts = problemFacts(problem, cards.data ?? [], technique)

  return (
    // spaced rather than dotted, as a row's counts are: a separator of its own
    // would start a line wherever the line wraps
    <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-meta text-muted-foreground">
      <Badge variant="outline" className="font-normal">
        {facts.difficulty}
      </Badge>
      <span>{facts.techniques}</span>
      <span>{facts.tried}</span>
      {facts.cardsLabel && (
        <span>
          {facts.cardsLabel}{' '}
          {facts.cards.map((card, index) => (
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
