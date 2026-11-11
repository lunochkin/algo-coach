import { FileX, Lock, RefreshCw, Trophy } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'

import {
  certCell,
  certId,
  certRows,
  CERTS_NONE,
  CERTS_NOTE,
  CERTS_TITLE,
  certStates,
  COURSE_SCOPE,
  levelName,
  levels,
  modulesInOrder,
  practiceShare,
  type CertStatus,
  type Course,
  coverageShare,
  PRACTICE,
  practiceLevel,
  BACK_KNOWLEDGE,
  OF,
  SCOPE_COLUMN,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PageSection } from '@/components/PageSection'
import { SectionBar } from '@/components/SectionBar'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { CertDialog } from '@/knowledge/CertDialog'
import { useLearner } from '@/knowledge/learner'
import { KNOWLEDGE } from '@/knowledge/paths'
import { StartSheet, type Scope } from '@/knowledge/StartSheet'
import { type Sections, useSections } from '@/lib/sections'
import { cn } from '@/lib/utils'

type Picked = { course: string; id: string }

// each module as a grid of scopes by level: `pages.md`, The knowledge pages
export function CertificationsPage() {
  const k = useKnowledge()
  const { catalog, board, order, certExams } = useLearner()
  const [params] = useSearchParams()
  // the home's ready certification opens on its conditions
  const [picked, setPicked] = useState<Picked | null>(() => {
    const id = params.get('open')
    const c = id ? catalog?.courses.find((x) => x.certs?.get(id)) : undefined
    return c && id ? { course: c.slug, id } : null
  })
  const [starting, setStarting] = useState<Scope | null>(null)

  const modules = useMemo(() => {
    if (!catalog || !board(null)) return undefined
    return modulesInOrder(catalog.courses, order, board, (c) => !!c.certs).map(({ c, b }) => ({
      c,
      b,
      states: certStates(b, c, certExams),
    }))
  }, [catalog, board, order, certExams])

  const shown = picked && modules?.find((m) => m.c.slug === picked.course)
  const sections = useSections((modules ?? []).map(({ c }) => ({ id: c.slug, label: c.title })))

  return (
    <section className="space-y-section">
      <PageHeader
        back={{ to: KNOWLEDGE, label: BACK_KNOWLEDGE }}
        title={CERTS_TITLE}
        note={CERTS_NOTE}
      />
      <Loaded of={OF.certifications} state={loadedFrom(k, modules)} blank={CERTS_NONE}>
        {(modules) => (
          <>
            <SectionBar items={sections.items} current={sections.current} onJump={sections.jump} />
            {modules.map(({ c, b, states }) => (
              <Grid
                key={c.slug}
                sections={sections}
                c={c}
                levels={levels(b.rules)}
                rules={b.rules}
                states={states}
                onPick={(id) => setPicked({ course: c.slug, id })}
              />
            ))}
          </>
        )}
      </Loaded>

      <CertDialog
        open={
          shown && picked ? { c: shown.c, b: shown.b, states: shown.states, id: picked.id } : null
        }
        onClose={() => setPicked(null)}
        onStart={setStarting}
      />
      <StartSheet scope={starting} onClose={() => setStarting(null)} />
    </section>
  )
}

function Grid(props: {
  sections: Sections
  c: Course
  levels: number[]
  rules: Parameters<typeof levelName>[0]
  states: Map<string, CertStatus>
  onPick: (id: string) => void
}) {
  const { c, states } = props
  const rows = certRows(c)
  return (
    <PageSection
      id={c.slug}
      title={c.title}
      count={rows.length}
      body="bare"
      closed={props.sections.closed(c.slug)}
      onToggle={props.sections.toggle}
    >
      <div className="overflow-x-auto rounded-xl border bg-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-meta text-muted-foreground">
              <th className="px-4 py-2 text-left font-normal">{SCOPE_COLUMN}</th>
              {props.levels.map((l) => (
                <th
                  key={l}
                  className={cn(
                    'px-2 py-2 text-center font-normal',
                    practiceLevel(c, l) && 'opacity-60',
                  )}
                >
                  {levelName(props.rules, l, true)}
                  {practiceLevel(c, l) && <span className="block">{PRACTICE}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((row) => (
              <tr key={row.scope}>
                <td className={cn('px-4 py-2', row.scope === COURSE_SCOPE && 'font-medium')}>
                  {row.title}
                </td>
                {props.levels.map((l) => {
                  const id = certId(c.slug, row.scope, l)
                  const s = states.get(id)
                  return (
                    <td key={l} className="px-1 py-1 text-center">
                      {s && s.state !== 'empty' ? (
                        <button
                          type="button"
                          onClick={() => props.onPick(id)}
                          className={cn(
                            'inline-flex size-11 items-center justify-center rounded-lg hover:bg-muted',
                            s.state === 'ready' && 'bg-brand-wash',
                          )}
                          aria-label={certCell(c.certs?.get(id)?.title ?? id, s)}
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
    </PageSection>
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
      return <span className="text-meta text-muted-foreground">{practiceShare(s)}</span>
    default:
      return (
        <span className="inline-flex flex-col items-center">
          <Ring coverage={s.coverage} retention={s.retention} />
          <span className="text-[10px] text-muted-foreground tabular-nums">
            {coverageShare(s.coverage)}
          </span>
        </span>
      )
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
