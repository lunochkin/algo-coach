import { Link, useSearchParams } from 'react-router'

import { api, type Listed } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickList } from '@/components/PickRow'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { lastAt, share } from '@/lib/format'
import { cn } from '@/lib/utils'

// the rows one page of the listing holds. The whole listing is fetched, since
// the tags count every problem the corpus carries, and a page is a slice of
// what the tags left
const PER_PAGE = 20

// every served problem at once, where the board reaches them one technique at
// a time. The techniques a problem carries are the filter
export function ProblemsPage() {
  const listed = useLoaded((signal) => api.GET('/api/problems', { signal }), 'problems')
  // the tags in the URL, so a filtered listing is a link the user can keep
  const [search, setSearch] = useSearchParams()
  const picked = search.getAll('technique')
  const page = Math.max(1, Number(search.get('page') ?? 1) || 1)

  // the tags and the page are the page's whole state, so one writer sets both
  function go(tags: string[], to: number) {
    const params = new URLSearchParams()
    for (const one of tags) params.append('technique', one)
    if (to > 1) params.set('page', String(to))
    setSearch(params)
  }

  // a tag moves the listing back to its first page: the page the reader was on
  // may hold nothing once the list is narrowed
  function toggle(technique: string) {
    go(
      picked.includes(technique)
        ? picked.filter((one) => one !== technique)
        : [...picked, technique],
      1,
    )
  }

  return (
    <section className="space-y-section">
      <PageHeader
        title="Problems"
        note="Every problem the engine has written. A tag narrows the list to the technique it names."
      />
      <Loaded of="the problems" state={listed} blank="No problem is served yet.">
        {(listed) => {
          const shown = picked.length === 0 ? listed : listed.filter((one) => carries(one, picked))
          const pages = Math.max(1, Math.ceil(shown.length / PER_PAGE))
          const current = Math.min(page, pages)
          const held = shown.slice((current - 1) * PER_PAGE, current * PER_PAGE)

          return (
            <div className="space-y-section">
              <section className="space-y-stack">
                <div className="flex flex-wrap gap-2">
                  {tags(listed).map(([technique, held]) => (
                    <button
                      key={technique}
                      type="button"
                      onClick={() => toggle(technique)}
                      aria-pressed={picked.includes(technique)}
                      className={cn(
                        'rounded-lg border px-2.5 py-1 font-mono text-meta transition-colors',
                        picked.includes(technique)
                          ? 'border-transparent bg-secondary text-secondary-foreground'
                          : 'hover:bg-accent',
                      )}
                    >
                      {technique}{' '}
                      <span className="font-sans text-muted-foreground tabular-nums">{held}</span>
                    </button>
                  ))}
                </div>
                {picked.length > 0 && (
                  <button
                    type="button"
                    onClick={() => go([], 1)}
                    className="text-meta text-muted-foreground underline-offset-4 hover:underline"
                  >
                    Clear {picked.length === 1 ? 'the tag' : `all ${picked.length} tags`}
                  </button>
                )}
              </section>

              <section className="space-y-stack">
                <h2 className="flex items-baseline gap-2 text-heading font-medium">
                  {picked.length === 0 ? 'Every problem' : 'Carrying a tag you picked'}
                  <span className="text-meta font-normal text-muted-foreground tabular-nums">
                    {shown.length}
                  </span>
                </h2>
                {shown.length === 0 ? (
                  <p className="text-meta text-muted-foreground">
                    No problem carries every technique you picked.
                  </p>
                ) : (
                  <>
                    <PickList>
                      {held.map((one) => (
                        <ProblemRow key={one.problem_id} listed={one} />
                      ))}
                    </PickList>
                    {pages > 1 && (
                      <div className="flex items-center gap-3 pt-1 text-meta text-muted-foreground">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={current === 1}
                          onClick={() => go(picked, current - 1)}
                        >
                          Previous
                        </Button>
                        <span className="tabular-nums">
                          Page {current} of {pages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={current === pages}
                          onClick={() => go(picked, current + 1)}
                        >
                          Next
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </section>
            </div>
          )
        }}
      </Loaded>
    </section>
  )
}

// the techniques read under the title, where a row's right-hand cluster is
// the counts: three badges and three counts on one line wrap into each other
function ProblemRow({ listed }: { listed: Listed }) {
  return (
    <Link
      to={`/problems/${encodeURIComponent(listed.problem_id)}?from=problems`}
      className="group -mx-3 block rounded-lg px-3 py-3 transition-colors hover:bg-accent"
    >
      <div className="flex items-baseline gap-3">
        <span className="font-medium underline-offset-4 group-hover:underline">
          {listed.title}
        </span>
        {listed.difficulty && (
          <Badge variant="outline" className="font-normal">
            {listed.difficulty}
          </Badge>
        )}
        <span className="ml-auto shrink-0 text-meta text-muted-foreground tabular-nums">
          {listed.attempt_count === 0
            ? "never attempted"
            : `${listed.attempt_count} attempts · ${share(listed.solved_count, listed.attempt_count)} solved · ${lastAt(listed.last_attempt_at)}`}
        </span>
      </div>
      <p className="mt-1 font-mono text-meta text-muted-foreground">
        {listed.techniques.join(" · ")}
      </p>
    </Link>
  )
}

// a problem is shown where it carries any tag the user picked: the tags
// narrow the list rather than asking for a problem carrying all of them
function carries(one: Listed, picked: string[]): boolean {
  return picked.some((technique) => one.techniques.includes(technique))
}

// every technique the listing holds, with how many problems carry it, most
// carried first
function tags(listed: Listed[]): [string, number][] {
  const held = new Map<string, number>()
  for (const one of listed)
    for (const technique of one.techniques)
      held.set(technique, (held.get(technique) ?? 0) + 1)
  return [...held].sort(([left, a], [right, b]) => b - a || left.localeCompare(right))
}
