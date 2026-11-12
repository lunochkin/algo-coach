import { Archive, Crosshair, Pause, Play } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'

import {
  moduleSummary,
  summary,
  ARCHIVE_BODY,
  ARCHIVE_KEEP,
  aimedAt,
  aimFocus,
  archiveTitle,
  type CellState,
  type CourseStatus,
  dueCount,
  type Focus,
  levelCountsLine,
  MODULE_ARCHIVE,
  moduleGrid,
  MODULE_FOCUS,
  MODULE_FOCUS_HERE,
  MODULE_FOCUSED,
  MODULE_GROUPS_TAB,
  MODULE_MAP_TAB,
  MODULE_MISSING,
  MODULE_PAUSE,
  MODULE_RESUME,
  MODULE_START,
  moduleMeta,
  noGraph,
  newRecord,
  BACK_KNOWLEDGE,
  OF,
  SUBTOPIC_COLUMN,
  BACK_BOARD,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PageSection } from '@/components/PageSection'
import { SectionBar } from '@/components/SectionBar'
import { Button } from '@/components/ui/button'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { ModuleMap } from '@/knowledge/ModuleMap'
import { StartSheet, type Scope } from '@/knowledge/StartSheet'
import { useSections } from '@/lib/sections'
import { GridTable } from '@/components/GridTable'
import { GRID_CELL, GRID_PRESS } from '@/lib/grid'
import { cn } from '@/lib/utils'

const HOME = '/knowledge'

// a covered group reads in the flame, as progress does; a group that cannot
// serve yet reads muted
const CELL_TONE: Record<CellState, string> = {
  covered: 'text-brand-deep font-medium',
  open: 'text-foreground',
  locked: 'text-muted-foreground',
  empty: 'text-muted-foreground',
}

// where each group of one module stands: `pages.md`, The knowledge pages
export function ModulePage() {
  const { module = '' } = useParams()
  // a module opened from the board returns there: `pages.md`, Sections
  const [params] = useSearchParams()
  const from = params.get('from')
  const k = useKnowledge()
  const navigate = useNavigate()
  const { catalog, focus, board, now, certExams } = useLearner()
  const [tab, setTab] = useState<'groups' | 'map'>(params.get('tab') === 'map' ? 'map' : 'groups')
  const [archiving, setArchiving] = useState(false)
  const [starting, setStarting] = useState<Scope | null>(null)

  const page = useMemo(() => {
    // named explicitly, so a paused module reads too
    const b = board(module)
    const c = b?.courses[0]
    if (!catalog || !b) return undefined
    return c ? { b, c } : null
  }, [catalog, board, module])
  const sections = useSections(
    page ? page.c.topics.map((t) => ({ id: t.slug, label: t.title })) : [],
  )

  function aim(f: Focus) {
    void k.add('focus', newRecord.focus(aimFocus(focus, f)))
  }

  function setStatus(status: CourseStatus) {
    void k.add('status', newRecord.status(module, status))
    // an archived module leaves the home and every page but its restore
    if (status === 'archived') navigate(HOME)
  }

  const aimed = (topic: string | null, sub: string | null) => aimedAt(focus, module, topic, sub)

  return (
    <section className="space-y-section">
      <PageHeader
        back={
          from === 'board' ? { to: '/', label: BACK_BOARD } : { to: HOME, label: BACK_KNOWLEDGE }
        }
        title={page?.c.title ?? module}
        // the lines identifying the module sit under its title, as every
        // page's note does, and read while the page loads too
        note={
          page && (
            <>
              <p>{moduleMeta(page.c.topics.length, dueCount(page.b, now), page.c.paused)}</p>
              <p>{moduleSummary(summary(page.b, now))}</p>
            </>
          )
        }
      />
      <Loaded
        of={OF.module}
        state={loadedFrom(k, page === undefined ? undefined : { page })}
        blank={MODULE_MISSING}
        blankWhen={(x) => x.page === null}
      >
        {({ page }) => {
          if (!page) return null
          const { b, c } = page
          const grid = moduleGrid(b, c)
          return (
            <section className="space-y-section">
              <div className="flex flex-wrap items-center gap-stack">
                <Button
                  onClick={() =>
                    setStarting({
                      course: module,
                      topic: null,
                      sub: null,
                      level: null,
                    })
                  }
                >
                  {MODULE_START}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={aimed(null, null)}
                  onClick={() => aim({ course: module, topic: null, sub: null })}
                >
                  <Crosshair />
                  {aimed(null, null) ? MODULE_FOCUSED : MODULE_FOCUS_HERE}
                </Button>
                {c.paused ? (
                  <>
                    <Button variant="outline" size="sm" onClick={() => setStatus('active')}>
                      <Play />
                      {MODULE_RESUME}
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setArchiving(true)}>
                      <Archive />
                      {MODULE_ARCHIVE}
                    </Button>
                  </>
                ) : (
                  <Button variant="outline" size="sm" onClick={() => setStatus('paused')}>
                    <Pause />
                    {MODULE_PAUSE}
                  </Button>
                )}
              </div>

              <p className="text-meta tabular-nums">{levelCountsLine(b, c)}</p>

              {/* the groups and the map are two tabs of one page: `pages.md`, The structure */}
              <ToggleGroup
                type="single"
                variant="outline"
                size="sm"
                value={tab}
                onValueChange={(v) => v && setTab(v as 'groups' | 'map')}
              >
                <ToggleGroupItem value="groups">{MODULE_GROUPS_TAB}</ToggleGroupItem>
                <ToggleGroupItem value="map">{MODULE_MAP_TAB}</ToggleGroupItem>
              </ToggleGroup>

              {tab === 'map' &&
                (c.graph ? (
                  <ModuleMap
                    c={c}
                    b={b}
                    focus={focus}
                    certExams={certExams}
                    onStart={setStarting}
                    onAim={(topic, sub) => aim({ course: module, topic, sub })}
                  />
                ) : (
                  <p className="text-meta text-muted-foreground">{noGraph(c)}</p>
                ))}

              {tab === 'groups' && (
                <SectionBar
                  items={sections.items}
                  current={sections.current}
                  onJump={sections.jump}
                />
              )}
              {tab === 'groups' &&
                grid.topics.map((t) => (
                  <PageSection
                    key={t.slug}
                    id={t.slug}
                    title={t.title}
                    count={t.count}
                    body="bare"
                    closed={sections.closed(t.slug)}
                    onToggle={sections.toggle}
                    aside={
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setStarting({
                              course: module,
                              topic: t.slug,
                              sub: null,
                              level: null,
                            })
                          }
                        >
                          <Play />
                          {MODULE_START}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={aimed(t.slug, null)}
                          onClick={() => aim({ course: module, topic: t.slug, sub: null })}
                        >
                          <Crosshair />
                          {aimed(t.slug, null) ? MODULE_FOCUSED : MODULE_FOCUS}
                        </Button>
                      </>
                    }
                  >
                    <GridTable
                      first={SUBTOPIC_COLUMN}
                      levels={grid.levels.map((l) => ({ key: l.level, head: l.name }))}
                    >
                      {t.rows.map((row) => (
                        <tr key={row.sub}>
                          <td className="px-4 py-2">
                            <div className="flex items-center gap-1">
                              {/* the name starts the subtopic at every level; the press beside it aims the focus */}
                              <button
                                type="button"
                                aria-label={row.start}
                                className={cn(
                                  'flex-1 text-left hover:underline',
                                  aimed(t.slug, row.sub) && 'font-medium text-brand-deep',
                                )}
                                onClick={() =>
                                  setStarting({
                                    course: module,
                                    topic: t.slug,
                                    sub: row.sub,
                                    level: null,
                                  })
                                }
                              >
                                {row.title}
                              </button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                aria-label={row.focus}
                                aria-pressed={aimed(t.slug, row.sub)}
                                onClick={() => aim({ course: module, topic: t.slug, sub: row.sub })}
                              >
                                <Crosshair
                                  className={cn(aimed(t.slug, row.sub) && 'text-brand-deep')}
                                />
                              </Button>
                            </div>
                          </td>
                          {row.cells.map(({ level, cell, label }) => (
                            <td key={level} className={GRID_CELL}>
                              {/* a locked cell starts too: locks do not apply to the filtered queue */}
                              <button
                                type="button"
                                disabled={cell.state === 'empty'}
                                className={cn(GRID_PRESS, CELL_TONE[cell.state])}
                                title={cell.line}
                                aria-label={label}
                                onClick={() =>
                                  setStarting({
                                    course: module,
                                    topic: t.slug,
                                    sub: row.sub,
                                    level,
                                  })
                                }
                              >
                                {cell.count}
                              </button>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </GridTable>
                  </PageSection>
                ))}

              <StartSheet scope={starting} onClose={() => setStarting(null)} />

              <AlertDialog open={archiving} onOpenChange={setArchiving}>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{archiveTitle(c.title)}</AlertDialogTitle>
                    <AlertDialogDescription>{ARCHIVE_BODY}</AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{ARCHIVE_KEEP}</AlertDialogCancel>
                    <AlertDialogAction onClick={() => setStatus('archived')}>
                      {MODULE_ARCHIVE}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </section>
          )
        }}
      </Loaded>
    </section>
  )
}
