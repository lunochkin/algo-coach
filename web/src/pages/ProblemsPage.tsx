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

// the three a problem carries, in the order a solver reads them rather than
// the order they count in
const LEVELS = ['easy', 'medium', 'hard']

// every served problem at once, where the board reaches them one technique at
// a time. The techniques a problem carries are the filter
export function ProblemsPage() {
  const listed = useLoaded((signal) => api.GET('/api/problems', { signal }), 'problems')
  // the tags in the URL, so a filtered listing is a link the user can keep
  const [search, setSearch] = useSearchParams()
  const picked = search.getAll('technique')
  const levels = search.getAll('difficulty')
  const page = Math.max(1, Number(search.get('page') ?? 1) || 1)

  // the two filters and the page are the page's whole state, so one writer
  // sets all three
  function go(tags: string[], asked: string[], to: number) {
    const params = new URLSearchParams()
    for (const one of tags) params.append('technique', one)
    for (const one of asked) params.append('difficulty', one)
    if (to > 1) params.set('page', String(to))
    setSearch(params)
  }

  // a filter moves the listing back to its first page: the page the reader was
  // on may hold nothing once the list is narrowed
  function toggle(technique: string) {
    go(without(picked, technique), levels, 1)
  }

  function toggleLevel(level: string) {
    go(picked, without(levels, level), 1)
  }

  return (
    <section className="space-y-section">
      <PageHeader
        title="Problems"
        note="Every problem the engine has written. A level and a tag narrow the list, and a problem shows where it matches both."
      />
      <Loaded of="the problems" state={listed} blank="No problem is served yet.">
        {(listed) => {
          // a filter of its own narrows what the other one counts, so each
          // count says what pressing that chip would leave
          const byLevel = listed.filter((one) => asked(one, levels))
          const byTag = listed.filter((one) => carries(one, picked))
          const shown = byLevel.filter((one) => carries(one, picked))
          const filtered = picked.length > 0 || levels.length > 0
          const pages = Math.max(1, Math.ceil(shown.length / PER_PAGE))
          const current = Math.min(page, pages)
          const held = shown.slice((current - 1) * PER_PAGE, current * PER_PAGE)

          return (
            <div className="space-y-section">
              <section className="space-y-stack">
                <div className="flex flex-wrap gap-2">
                  {LEVELS.map((level) => (
                    <button
                      key={level}
                      type="button"
                      onClick={() => toggleLevel(level)}
                      aria-pressed={levels.includes(level)}
                      className={cn(
                        'rounded-lg border px-2.5 py-1 text-meta transition-colors',
                        levels.includes(level)
                          ? 'border-transparent bg-secondary text-secondary-foreground'
                          : 'hover:bg-accent',
                      )}
                    >
                      {level}{' '}
                      <span className="inline-block min-w-[2ch] text-right text-muted-foreground tabular-nums">
                        {byTag.filter((one) => one.difficulty === level).length}
                      </span>
                    </button>
                  ))}
                </div>

                <div className="flex flex-wrap gap-2">
                  {tags(listed, byLevel).map(([technique, held]) => (
                    <button
                      key={technique}
                      type="button"
                      onClick={() => toggle(technique)}
                      aria-pressed={picked.includes(technique)}
                      className={cn(
                        'rounded-lg border px-2.5 py-1 text-meta transition-colors',
                        picked.includes(technique)
                          ? 'border-transparent bg-secondary text-secondary-foreground'
                          : 'hover:bg-accent',
                      )}
                    >
                      {technique}{' '}
                      <span className="inline-block min-w-[2ch] text-right text-muted-foreground tabular-nums">
                        {held}
                      </span>
                    </button>
                  ))}
                </div>

              </section>

              <section className="space-y-stack">
                <h2 className="flex items-baseline gap-2 text-heading font-medium">
                  {filtered ? 'Matching your filters' : 'Every problem'}
                  <span className="text-meta font-normal text-muted-foreground tabular-nums">
                    {shown.length}
                  </span>
                  {filtered && (
                    <button
                      type="button"
                      onClick={() => go([], [], 1)}
                      className="ml-auto text-meta font-normal text-muted-foreground underline-offset-4 hover:underline"
                    >
                      Clear{' '}
                      {picked.length + levels.length === 1
                        ? 'the filter'
                        : `all ${picked.length + levels.length} filters`}
                    </button>
                  )}
                </h2>
                {shown.length === 0 ? (
                  <p className="text-meta text-muted-foreground">
                    No problem carries a tag you picked at the level you asked for.
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
                          onClick={() => go(picked, levels, current - 1)}
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
                          onClick={() => go(picked, levels, current + 1)}
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
  return picked.length === 0 || picked.some((technique) => one.techniques.includes(technique))
}

// the levels read the same way, and the two filters meet: a problem shows
// where it carries a picked tag and sits at a level asked for
function asked(one: Listed, levels: string[]): boolean {
  return levels.length === 0 || (one.difficulty !== null && levels.includes(one.difficulty))
}

// a chip that presses off where it is on
function without(held: string[], one: string): string[] {
  return held.includes(one) ? held.filter((other) => other !== one) : [...held, one]
}

// every technique the listing holds, ordered by how many problems carry it in
// the whole listing, and counted over what the level filter left. The order is
// the whole listing's so the rows never rewrap as a count moves
function tags(all: Listed[], left: Listed[]): [string, number][] {
  const order = held(all)
  const counted = held(left)
  return [...order]
    .sort(([one, a], [other, b]) => b - a || one.localeCompare(other))
    .map(([technique]) => [technique, counted.get(technique) ?? 0])
}

function held(listed: Listed[]): Map<string, number> {
  const counted = new Map<string, number>()
  for (const one of listed)
    for (const technique of one.techniques)
      counted.set(technique, (counted.get(technique) ?? 0) + 1)
  return counted
}
