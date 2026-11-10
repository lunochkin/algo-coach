import { FileX, Lock, RefreshCw, Target, Trophy } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'

import {
  bySavedOrder,
  certConditions,
  certFocus,
  certId,
  certStates,
  COURSE_SCOPE,
  focusLine,
  levelName,
  levels,
  STATE_LABEL,
  type CertStatus,
  type Course,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { KNOWLEDGE } from '@/knowledge/paths'
import { StartSheet, type Scope } from '@/knowledge/StartSheet'
import { cn } from '@/lib/utils'

type Picked = { course: string; id: string }

// each module as a grid of scopes by level: `pages.md`, The knowledge pages
export function CertificationsPage() {
  const k = useKnowledge()
  const { catalog, board, order, certExams, focus } = useLearner()
  const [params] = useSearchParams()
  // the home's ready certification opens on its conditions
  const [picked, setPicked] = useState<Picked | null>(() => {
    const id = params.get('open')
    const c = id ? catalog?.courses.find((x) => x.certs?.get(id)) : undefined
    return c && id ? { course: c.slug, id } : null
  })
  const [starting, setStarting] = useState<Scope | null>(null)

  const modules = useMemo(() => {
    const b = board(null)
    if (!catalog || !b) return undefined
    return bySavedOrder(catalog.courses.filter((c) => c.certs), (c) => c.slug, order).map((c) => {
      const own = board(c.slug)!
      return { c, b: own, states: certStates(own, c, certExams) }
    })
  }, [catalog, board, order, certExams])

  const shown = picked && modules?.find((m) => m.c.slug === picked.course)
  const v = shown ? certConditions(shown.b, shown.c, picked.id, shown.states, focus) : null

  return (
    <section className="space-y-section">
      <PageHeader
        back={{ to: KNOWLEDGE, label: 'Knowledge' }}
        title="Certifications"
        note="Rings: coverage outside, retention inside. A certification opens on its conditions."
      />
      <Loaded of="the certifications" state={loadedFrom(k, modules)} blank="No module carries certifications yet.">
        {(modules) => (
          <>
            {modules.map(({ c, b, states }) => (
              <Grid key={c.slug} c={c} levels={levels(b.rules)} rules={b.rules} states={states} onPick={(id) => setPicked({ course: c.slug, id })} />
            ))}
          </>
        )}
      </Loaded>

      <Dialog open={!!v} onOpenChange={(open) => !open && setPicked(null)}>
        <DialogContent>
          {v && shown && picked && (
            <>
              <DialogHeader>
                <DialogTitle>{v.title}</DialogTitle>
              </DialogHeader>
              <div className="space-y-stack text-meta">
                <p className="font-medium text-brand-deep">{v.label}</p>
                {v.note && <p>{v.note}</p>}
                {v.progressNote && <p className="text-muted-foreground">{v.progressNote}</p>}
                <ul className="space-y-1">
                  {v.checks.map((x) => (
                    <li key={x.text}>
                      <span className={x.ok ? 'text-verdict-passed' : 'text-verdict-wrong'}>{x.ok ? '✓' : '✗'} </span>
                      {x.text}
                    </li>
                  ))}
                </ul>
                {v.short.length > 0 && (
                  <div className="space-y-1">
                    <p className="font-medium">To cover</p>
                    {v.short.map((g) => (
                      <div key={g.sub} className="flex items-center gap-stack">
                        <span className="flex-1">{g.line}</span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const level = shown.c.certs?.get(picked.id)?.level ?? null
                            setPicked(null)
                            setStarting({ course: shown.c.slug, topic: g.topic, sub: g.sub, level })
                          }}
                        >
                          Start
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-muted-foreground">{v.scope}</p>
              </div>
              <DialogFooter>
                {v.offersTarget &&
                  (v.targeted ? (
                    <Button variant="outline" onClick={() => void k.add('focus', focusLine(null))}>
                      Untarget
                    </Button>
                  ) : (
                    <Button
                      variant={v.offersExam ? 'outline' : 'default'}
                      onClick={() => {
                        const f = certFocus(shown.c, picked.id, !!focus?.strict)
                        if (f) void k.add('focus', focusLine(f))
                        setPicked(null)
                      }}
                    >
                      <Target />
                      Target
                    </Button>
                  ))}
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
      <StartSheet scope={starting} onClose={() => setStarting(null)} />
    </section>
  )
}

function Grid(props: {
  c: Course
  levels: number[]
  rules: Parameters<typeof levelName>[0]
  states: Map<string, CertStatus>
  onPick: (id: string) => void
}) {
  const { c, states } = props
  const rows = [...c.topics.map((t) => ({ scope: t.slug, title: t.title })), { scope: COURSE_SCOPE, title: c.title }]
  return (
    <section className="space-y-stack">
      <h2 className="text-heading font-medium">{c.title}</h2>
      <div className="overflow-x-auto rounded-xl border bg-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-meta text-muted-foreground">
              <th className="px-4 py-2 text-left font-normal">Scope</th>
              {props.levels.map((l) => (
                <th key={l} className="px-2 py-2 text-center font-normal">
                  {levelName(props.rules, l, true)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((row) => (
              <tr key={row.scope}>
                <td className={cn('px-4 py-2', row.scope === COURSE_SCOPE && 'font-medium')}>{row.title}</td>
                {props.levels.map((l) => {
                  const id = certId(c.slug, row.scope, l)
                  const s = states.get(id)
                  return (
                    <td key={l} className="px-1 py-1 text-center">
                      {s && s.state !== 'empty' ? (
                        <button
                          type="button"
                          onClick={() => props.onPick(id)}
                          className={cn('inline-flex size-11 items-center justify-center rounded-lg hover:bg-muted', s.state === 'ready' && 'bg-brand-wash')}
                          aria-label={`${c.certs?.get(id)?.title ?? id}: ${s.state === 'not_certified' ? `practice only, ${s.passed} of ${s.questions} passed` : STATE_LABEL[s.state]}`}
                        >
                          <Cell s={s} />
                        </button>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// one shape per state, as the phone's grid draws them
function Cell({ s }: { s: CertStatus }) {
  switch (s.state) {
    case 'earned':
      return <Trophy className="size-5 fill-brand text-brand" />
    case 'ready':
      return <Trophy className="size-5 text-brand-deep" />
    case 'locked':
      return <Lock className="size-4 text-muted-foreground" />
    case 'needs_refresh':
      return <RefreshCw className="size-4 text-brand" />
    case 'insufficient_pool':
      return <FileX className="size-4 text-brand" />
    case 'not_certified':
      return <span className="text-meta text-muted-foreground">{s.questions ? `${s.passed}/${s.questions}` : '—'}</span>
    default:
      return <Ring coverage={s.coverage} retention={s.retention} />
  }
}

function Ring({ coverage, retention }: { coverage: number; retention: number }) {
  const arc = (r: number, share: number) => {
    const len = 2 * Math.PI * r
    return (
      <>
        <circle cx={16} cy={16} r={r} fill="none" strokeWidth={3} className="stroke-border" />
        <circle
          cx={16}
          cy={16}
          r={r}
          fill="none"
          strokeWidth={3}
          className="stroke-brand"
          strokeDasharray={`${len * Math.max(0, Math.min(1, share))} ${len}`}
          transform="rotate(-90 16 16)"
        />
      </>
    )
  }
  return (
    <svg width={32} height={32} aria-hidden>
      {arc(13, coverage)}
      {arc(8, retention)}
    </svg>
  )
}
