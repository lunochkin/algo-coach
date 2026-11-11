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
  OF,
} from '@algo-coach/core'
import { useSearchParams } from 'react-router'

import { api, type Listed } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { PickPanel, PickRow } from '@/components/PickRow'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { counts } from '@/lib/format'

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
      <Loaded of={OF.problems} state={listed} blank={PROBLEMS_NONE}>
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
                  // the filters are toggles, drawn as every toggle on the pages is
                  <ToggleGroup
                    key={kind}
                    type="multiple"
                    variant="outline"
                    size="sm"
                    className="w-auto flex-wrap"
                    value={chips.filter((chip) => chip.on).map((chip) => chip.name)}
                  >
                    {chips.map((chip) => (
                      <ToggleGroupItem
                        key={chip.name}
                        value={chip.name}
                        onClick={() => go(toggled(filter, kind, chip.name))}
                      >
                        {chip.name}
                        <span className="inline-block min-w-[2ch] text-right text-muted-foreground tabular-nums">
                          {chip.count}
                        </span>
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                ))}
              </section>

              <section className="space-y-stack">
                <SectionHeading
                  title={listingHeading(view.filtered)}
                  count={view.shown}
                  aside={
                    view.filtered && (
                      <button
                        type="button"
                        onClick={() => go(NO_FILTER)}
                        className="text-meta text-muted-foreground underline-offset-4 hover:underline"
                      >
                        {clearFilters(filter)}
                      </button>
                    )
                  }
                />
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
                      <div className="flex items-center gap-stack pt-1 text-meta text-muted-foreground">
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
