import { Crosshair, Pause, Play } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

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
  focusOn,
  groupCell,
  levelCounts,
  levelName,
  levels,
  MODULE_ARCHIVE,
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
  startGroup,
  subsByDepth,
  subTitle,
  newRecord,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
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
  const k = useKnowledge()
  const navigate = useNavigate()
  const { catalog, focus, board, now, certExams } = useLearner()
  const [tab, setTab] = useState<'groups' | 'map'>('groups')
  const [archiving, setArchiving] = useState(false)
  const [starting, setStarting] = useState<Scope | null>(null)

  const page = useMemo(() => {
    // named explicitly, so a paused module reads too
    const b = board(module)
    const c = b?.courses[0]
    if (!catalog || !b) return undefined
    return c ? { b, c } : null
  }, [catalog, board, module])

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
      <PageHeader back={{ to: HOME, label: 'Knowledge' }} title={page?.c.title ?? module} />
      <Loaded
        of="the module"
        state={loadedFrom(k, page === undefined ? undefined : { page })}
        blank={MODULE_MISSING}
        blankWhen={(x) => x.page === null}
      >
        {({ page }) => {
          if (!page) return null
          const { b, c } = page
          const lv = levels(b.rules)
          const due = dueCount(b, now)
          return (
            <section className="space-y-section">
              <div className="flex flex-wrap items-center gap-stack">
                <div className="flex-1 text-meta text-muted-foreground">
                  <p>{moduleMeta(c.topics.length, due, c.paused)}</p>
                  <p>{moduleSummary(summary(b, now))}</p>
                </div>
                <Button
                  size="sm"
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

              <p className="flex flex-wrap gap-x-4 text-meta">
                {levelCounts(b, c).map((x) =>
                  x.total ? (
                    <span key={x.level}>
                      {x.name}{' '}
                      <span className="tabular-nums">
                        {x.passed}/{x.total}
                      </span>
                    </span>
                  ) : null,
                )}
              </p>

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

              {tab === 'groups' &&
                c.topics.map((t) => (
                  <section key={t.slug} className="space-y-stack">
                    <SectionHeading
                      title={t.title}
                      count={t.subs.length}
                      aside={
                        <>
                          <Button
                            variant="outline"
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
                            {MODULE_START}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={aimed(t.slug, null)}
                            onClick={() => aim({ course: module, topic: t.slug, sub: null })}
                          >
                            {aimed(t.slug, null) ? MODULE_FOCUSED : MODULE_FOCUS}
                          </Button>
                        </>
                      }
                    />
                    <div className="overflow-x-auto rounded-xl border bg-card">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-meta text-muted-foreground">
                            <th className="px-4 py-2 text-left font-normal">Subtopic</th>
                            {lv.map((level) => (
                              <th key={level} className="px-3 py-2 text-right font-normal">
                                {levelName(b.rules, level, true)}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {subsByDepth(c, t).map((sub) => (
                            <tr key={sub}>
                              <td className="px-4 py-2">
                                <div className="flex items-center gap-1">
                                  {/* the name starts the subtopic at every level; the press beside it aims the focus */}
                                  <button
                                    type="button"
                                    className={cn(
                                      'flex-1 text-left hover:underline',
                                      aimed(t.slug, sub) && 'font-medium text-brand-deep',
                                    )}
                                    onClick={() =>
                                      setStarting({
                                        course: module,
                                        topic: t.slug,
                                        sub,
                                        level: null,
                                      })
                                    }
                                  >
                                    {subTitle(c, sub)}
                                  </button>
                                  <Button
                                    variant="ghost"
                                    size="icon-sm"
                                    aria-label={focusOn(subTitle(c, sub))}
                                    aria-pressed={aimed(t.slug, sub)}
                                    onClick={() => aim({ course: module, topic: t.slug, sub })}
                                  >
                                    <Crosshair
                                      className={cn(aimed(t.slug, sub) && 'text-brand-deep')}
                                    />
                                  </Button>
                                </div>
                              </td>
                              {lv.map((level) => {
                                const cell = groupCell(b, {
                                  course: c.slug,
                                  topic: t.slug,
                                  sub,
                                  level,
                                })
                                return (
                                  <td key={level} className="px-1 py-1 text-right">
                                    {/* a locked cell starts too: locks do not apply to the filtered queue */}
                                    <button
                                      type="button"
                                      disabled={cell.state === 'empty'}
                                      className={cn(
                                        'rounded-md px-2 py-1 tabular-nums hover:bg-muted disabled:hover:bg-transparent',
                                        CELL_TONE[cell.state],
                                      )}
                                      title={cell.line}
                                      aria-label={startGroup(
                                        subTitle(c, sub),
                                        levelName(b.rules, level),
                                        cell.line,
                                      )}
                                      onClick={() =>
                                        setStarting({
                                          course: module,
                                          topic: t.slug,
                                          sub,
                                          level,
                                        })
                                      }
                                    >
                                      {cell.count}
                                    </button>
                                  </td>
                                )
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
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
