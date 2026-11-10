import { Crosshair, Pause, Play } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import {
  focusLine,
  groupCell,
  levelCounts,
  levelName,
  levels,
  subsByDepth,
  subTitle,
  type CellState,
  type CourseStatus,
  type Focus,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
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
  const { catalog, focus, board, now } = useLearner()
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
    void k.add('focus', focusLine({ ...f, strict: !!focus?.strict }))
  }

  function setStatus(status: CourseStatus) {
    void k.add('status', { course: module, status })
    // an archived module leaves the home and every page but its restore
    if (status === 'archived') navigate(HOME)
  }

  const aimedAt = (topic: string | null, sub: string | null) =>
    focus?.course === module && !focus.cert && focus.topic === topic && focus.sub === sub

  return (
    <Loaded
      of="the module"
      state={loadedFrom(k, page === undefined ? undefined : { page })}
      blank="No module of that name is open: it may be archived."
      blankWhen={(x) => x.page === null}
    >
      {({ page }) => {
        if (!page) return null
        const { b, c } = page
        const lv = levels(b.rules)
        const due = b.questions().filter((q) => b.toReview(q, now)).length
        return (
          <section className="space-y-section">
            <PageHeader back={{ to: HOME, label: 'Knowledge' }} title={c.title} />
            <div className="flex flex-wrap items-center gap-stack">
              <p className="flex-1 text-meta text-muted-foreground">
                {c.topics.length} topics · {due} due · {c.paused ? 'paused' : 'active'}
              </p>
              <Button size="sm" onClick={() => setStarting({ course: module, topic: null, sub: null, level: null })}>
                Start
              </Button>
              <Button variant="outline" size="sm" disabled={aimedAt(null, null)} onClick={() => aim({ course: module, topic: null, sub: null })}>
                <Crosshair />
                {aimedAt(null, null) ? 'Focused' : 'Focus here'}
              </Button>
              {c.paused ? (
                <>
                  <Button variant="outline" size="sm" onClick={() => setStatus('active')}>
                    <Play />
                    Resume
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setArchiving(true)}>
                    Archive
                  </Button>
                </>
              ) : (
                <Button variant="outline" size="sm" onClick={() => setStatus('paused')}>
                  <Pause />
                  Pause
                </Button>
              )}
            </div>

            <p className="flex flex-wrap gap-x-4 text-meta">
              {levelCounts(b, c).map((x) =>
                x.total ? (
                  <span key={x.level}>
                    {x.name} <span className="tabular-nums">{x.passed}/{x.total}</span>
                  </span>
                ) : null,
              )}
            </p>

            {c.topics.map((t) => (
              <section key={t.slug} className="space-y-stack">
                <div className="flex items-baseline gap-stack">
                  <h2 className="flex-1 text-heading font-medium">
                    {t.title}
                    <span className="ml-2 text-meta font-normal text-muted-foreground">{t.subs.length} subtopics</span>
                  </h2>
                  <Button variant="outline" size="sm" onClick={() => setStarting({ course: module, topic: t.slug, sub: null, level: null })}>
                    Start
                  </Button>
                  <Button variant="ghost" size="sm" disabled={aimedAt(t.slug, null)} onClick={() => aim({ course: module, topic: t.slug, sub: null })}>
                    {aimedAt(t.slug, null) ? 'Focused' : 'Focus'}
                  </Button>
                </div>
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
                                className={cn('flex-1 text-left hover:underline', aimedAt(t.slug, sub) && 'font-medium text-brand-deep')}
                                onClick={() => setStarting({ course: module, topic: t.slug, sub, level: null })}
                              >
                                {subTitle(c, sub)}
                              </button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                aria-label={`Focus on ${subTitle(c, sub)}`}
                                aria-pressed={aimedAt(t.slug, sub)}
                                onClick={() => aim({ course: module, topic: t.slug, sub })}
                              >
                                <Crosshair className={cn(aimedAt(t.slug, sub) && 'text-brand-deep')} />
                              </Button>
                            </div>
                          </td>
                          {lv.map((level) => {
                            const cell = groupCell(b, { course: c.slug, topic: t.slug, sub, level })
                            return (
                              <td key={level} className="px-1 py-1 text-right">
                                {/* a locked cell starts too: locks do not apply to the filtered queue */}
                                <button
                                  type="button"
                                  disabled={cell.state === 'empty'}
                                  className={cn('rounded-md px-2 py-1 tabular-nums hover:bg-muted disabled:hover:bg-transparent', CELL_TONE[cell.state])}
                                  title={cell.line}
                                  aria-label={`Start ${subTitle(c, sub)}, ${levelName(b.rules, level)}: ${cell.line}`}
                                  onClick={() => setStarting({ course: module, topic: t.slug, sub, level })}
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
                  <AlertDialogTitle>Archive {c.title}?</AlertDialogTitle>
                  <AlertDialogDescription>
                    An archived module leaves the home and every queue. Its answers stay, and restoring it loses
                    nothing.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Keep it</AlertDialogCancel>
                  <AlertDialogAction onClick={() => setStatus('archived')}>Archive</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </section>
        )
      }}
    </Loaded>
  )
}
