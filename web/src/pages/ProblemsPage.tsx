import {
  clearFilters,
  listingHeading,
  listingView,
  NO_FILTER,
  PAGE_NEXT,
  PAGE_PREVIOUS,
  pageOf,
  PROBLEMS_NONE,
  PROBLEMS_NONE_MATCH,
  PROBLEMS_NOTE,
  PROBLEMS_TITLE,
  toggled,
  type ListingFilter,
} from '@algo-coach/core'
import { useSearchParams } from 'react-router'

import { api, type Listed } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickPanel, PickRow } from '@/components/PickRow'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { counts } from '@/lib/format'
import { cn } from '@/lib/utils'

// every served problem at once, where the board reaches them one technique at
// a time. Core reads the filters, the counts and the page: `listingView`
export function ProblemsPage() {
  const listed = useLoaded((signal) => api.GET('/api/problems', { signal }), 'problems')
  // the filters and the page in the URL, so a filtered listing is a link the user can keep
  const [search, setSearch] = useSearchParams()
  const filter: ListingFilter = {
    techniques: search.getAll('technique'),
    difficulties: search.getAll('difficulty'),
    page: Math.max(1, Number(search.get('page') ?? 1) || 1),
  }

  function go(next: ListingFilter) {
    const params = new URLSearchParams()
    for (const one of next.techniques) params.append('technique', one)
    for (const one of next.difficulties) params.append('difficulty', one)
    if (next.page > 1) params.set('page', String(next.page))
    setSearch(params)
  }

  return (
    <section className="space-y-section">
      <PageHeader title={PROBLEMS_TITLE} note={PROBLEMS_NOTE} />
      <Loaded of="the problems" state={listed} blank={PROBLEMS_NONE}>
        {(listed) => {
          const view = listingView(listed, filter)
          return (
            <div className="space-y-section">
              <section className="space-y-stack">
                {(
                  [
                    ['difficulties', view.difficulties],
                    ['techniques', view.tags],
                  ] as const
                ).map(([kind, chips]) => (
                  <div key={kind} className="flex flex-wrap gap-2">
                    {chips.map((chip) => (
                      <button
                        key={chip.name}
                        type="button"
                        onClick={() => go(toggled(filter, kind, chip.name))}
                        aria-pressed={chip.on}
                        className={cn(
                          'rounded-lg border px-2.5 py-1 text-meta transition-colors',
                          chip.on
                            ? 'border-transparent bg-secondary text-secondary-foreground'
                            : 'hover:bg-accent',
                        )}
                      >
                        {chip.name}{' '}
                        <span className="inline-block min-w-[2ch] text-right text-muted-foreground tabular-nums">
                          {chip.count}
                        </span>
                      </button>
                    ))}
                  </div>
                ))}
              </section>

              <section className="space-y-stack">
                <h2 className="flex items-baseline gap-2 text-heading font-medium">
                  {listingHeading(view.filtered)}
                  <span className="text-meta font-normal text-muted-foreground tabular-nums">
                    {view.shown}
                  </span>
                  {view.filtered && (
                    <button
                      type="button"
                      onClick={() => go(NO_FILTER)}
                      className="ml-auto text-meta font-normal text-muted-foreground underline-offset-4 hover:underline"
                    >
                      {clearFilters(filter)}
                    </button>
                  )}
                </h2>
                {view.shown === 0 ? (
                  <p className="text-meta text-muted-foreground">{PROBLEMS_NONE_MATCH}</p>
                ) : (
                  <>
                    <PickPanel>
                      {view.rows.map((one) => (
                        <ProblemRow key={one.problem_id} listed={one} drilled={view.drilled} />
                      ))}
                    </PickPanel>
                    {view.pages > 1 && (
                      <div className="flex items-center gap-3 pt-1 text-meta text-muted-foreground">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={view.page === 1}
                          onClick={() => go({ ...filter, page: view.page - 1 })}
                        >
                          {PAGE_PREVIOUS}
                        </Button>
                        <span className="tabular-nums">{pageOf(view.page, view.pages)}</span>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={view.page === view.pages}
                          onClick={() => go({ ...filter, page: view.page + 1 })}
                        >
                          {PAGE_NEXT}
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
// the counts. `drilled` is the one tag the listing is filtered to, which the
// claim then ticks as a pick from the board ticks its technique
function ProblemRow({ listed, drilled }: { listed: Listed; drilled: string | null }) {
  const query = new URLSearchParams({ from: 'problems' })
  if (drilled !== null) query.set('technique', drilled)
  return (
    <PickRow
      to={`/problems/${encodeURIComponent(listed.problem_id)}?${query.toString()}`}
      title={listed.title}
      badge={
        listed.difficulty && (
          <Badge variant="outline" className="font-normal">
            {listed.difficulty}
          </Badge>
        )
      }
      stats={counts(listed)}
      note={listed.techniques.join(' · ')}
      mono
    />
  )
}
