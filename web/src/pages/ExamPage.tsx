import { X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import {
  certExam,
  examOpening,
  examOutcome,
  examPool,
  examTitle,
  LETTERS,
  levelExam,
  levelExamLabel,
  levelName,
  levels,
  questionHead,
  setting,
  validSetting,
  youLine,
  type Catalog,
  type ExamPlan,
  type Result,
  type SettingRecord,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Ask, Details, Verdict } from '@/knowledge/Ask'
import { linesOf, loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { CERTIFICATIONS, KNOWLEDGE } from '@/knowledge/paths'
import { cn } from '@/lib/utils'

const ALL = 'all'

// an exam's choices, the exam itself and its results, on one page: the sample
// is drawn at the start, so a reload returns to the choices. `pages.md`, The
// knowledge pages
export function ExamPage() {
  const k = useKnowledge()
  const learner = useLearner()
  const [params] = useSearchParams()
  const [plan, setPlan] = useState<ExamPlan | null>(null)
  const cert = params.get('cert')

  return (
    <Loaded of="the exam" state={loadedFrom(k, learner.catalog ?? undefined)}>
      {(catalog) =>
        plan ? (
          <Running plan={plan} catalog={catalog} back={cert ? CERTIFICATIONS : KNOWLEDGE} />
        ) : cert ? (
          <CertChoice id={cert} catalog={catalog} onStart={setPlan} />
        ) : (
          <LevelChoice catalog={catalog} onStart={setPlan} />
        )
      }
    </Loaded>
  )
}

function LevelChoice({ catalog, onStart }: { catalog: Catalog; onStart: (p: ExamPlan) => void }) {
  const k = useKnowledge()
  const { focus, board } = useLearner()
  // opens on the focus, which the phone and the web share
  const [opening] = useState(() => examOpening(focus))
  const [course, setCourse] = useState<string | null>(opening.course)
  const [level, setLevel] = useState(opening.level)
  const stored = setting(linesOf<SettingRecord>(k.records, 'setting'), 'exam_size')
  const [size, setSize] = useState(String(stored))
  const b = useMemo(() => board(course), [board, course])
  const pool = useMemo(() => (b ? examPool(b, level).length : 0), [b, level])
  const n = Number(size)
  const count = validSetting('exam_size', n) ? Math.min(n, pool) : 0

  // the size is a setting, saved shortly after typing stops, as the phone saves it
  useEffect(() => {
    if (!validSetting('exam_size', n) || n === stored) return
    const t = setTimeout(() => void k.add('setting', { name: 'exam_size', n }), 600)
    return () => clearTimeout(t)
  }, [n, stored, k])

  return (
    <section className="space-y-section">
      <PageHeader back={{ to: KNOWLEDGE, label: 'Knowledge' }} title="Exam" note="No feedback until the end." />
      <div className="space-y-stack">
        <Choice label="Module">
          <ToggleGroup type="single" variant="outline" size="sm" className="w-auto flex-wrap" value={course ?? ALL} onValueChange={(v) => v && setCourse(v === ALL ? null : v)}>
            <ToggleGroupItem value={ALL}>All</ToggleGroupItem>
            {catalog.courses.map((c) => (
              <ToggleGroupItem key={c.slug} value={c.slug}>
                {c.title}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </Choice>
        <Choice label="Level">
          <ToggleGroup type="single" variant="outline" size="sm" className="w-auto flex-wrap" value={String(level)} onValueChange={(v) => v && setLevel(Number(v))}>
            {levels(catalog.rules).map((l) => (
              <ToggleGroupItem key={l} value={String(l)}>
                {levelName(catalog.rules, l)}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
          <p className="text-meta text-muted-foreground">{catalog.rules.levels[level] ?? ''}</p>
        </Choice>
        <div className="flex items-center gap-stack">
          <Label htmlFor="exam-size">Questions</Label>
          <Input id="exam-size" inputMode="numeric" className="w-24 tabular-nums" value={size} aria-invalid={!validSetting('exam_size', n)} onChange={(e) => setSize(e.target.value)} />
        </div>
        <Button disabled={!b || !count} onClick={() => b && onStart(levelExam(b, level, n))}>
          {levelExamLabel(catalog.rules, level, pool, count)}
        </Button>
      </div>
    </section>
  )
}

function CertChoice({ id, catalog, onStart }: { id: string; catalog: Catalog; onStart: (p: ExamPlan) => void }) {
  const { board } = useLearner()
  const c = catalog.courses.find((x) => x.certs?.get(id))
  const x = c?.certs?.get(id)
  const b = c ? board(c.slug) : null
  return (
    <section className="space-y-section">
      <PageHeader back={{ to: CERTIFICATIONS, label: 'Certifications' }} title={x?.title ?? 'Exam'} note="No feedback until the end." />
      {c && x && b ? (
        <Panel>
          <p>
            {x.rule.size} questions, pass {Math.round(x.rule.passShare * 100)}%. Stopping before the last question
            stores the exam as not passed.
          </p>
          <div>
            <Button onClick={() => { const p = certExam(b, c, id); if (p) onStart(p) }}>Start the exam</Button>
          </div>
        </Panel>
      ) : (
        <p className="text-meta text-muted-foreground">No certification of that name is open.</p>
      )}
    </section>
  )
}

function Choice({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <p className="text-meta text-muted-foreground">{label}</p>
      {children}
    </div>
  )
}

type Phase = 'ask' | 'review' | 'done'

function Running({ plan, catalog, back }: { plan: ExamPlan; catalog: Catalog; back: string }) {
  const k = useKnowledge()
  const [index, setIndex] = useState(0)
  const [phase, setPhase] = useState<Phase>('ask')
  const [reviewAt, setReviewAt] = useState(0)
  const [results, setResults] = useState<Result[]>([])
  const answered = useRef<Result[]>([])
  const ended = useRef(false)
  const total = plan.questions.length
  const out = examOutcome(plan, results, '', catalog.courses)

  // the answers, the stint and a certification's record are stored together at the end
  function end() {
    if (ended.current) return
    ended.current = true
    const rs = answered.current
    if (!rs.length) return
    const done = examOutcome(plan, rs, new Date().toISOString(), catalog.courses)
    for (const a of done.attempts) void k.add('attempt', { ...a })
    void k.add('session', { mode: plan.mode, score: done.score, n: done.n })
    if (done.cert) void k.add('cert', done.cert)
  }

  // leaving through the navigation ends the exam the same way; a closed tab leaves no record
  const leave = useRef(end)
  useEffect(() => {
    leave.current = end
  })
  useEffect(() => {
    ended.current = false
    return () => leave.current()
  }, [])

  function finish() {
    end()
    setPhase('done')
  }

  const q = plan.questions[index]
  const course = q ? catalog.courses.find((c) => c.slug === q.course) : undefined

  return (
    <section className="space-y-section">
      <header className="flex items-center gap-stack">
        <h1 className="flex-1 text-title font-semibold">{examTitle(phase, index, total, reviewAt, out.missed.length)}</h1>
        {phase !== 'ask' && (
          <span className="text-meta tabular-nums">
            {out.score}/{out.n}
          </span>
        )}
        {phase === 'ask' && (
          <Button variant="outline" size="sm" onClick={finish}>
            <X />
            Stop
          </Button>
        )}
      </header>

      {phase === 'ask' && q ? (
        <Ask
          key={index}
          q={q}
          course={course}
          head={questionHead(course, catalog.rules, q, '', false)}
          exam={{ last: index + 1 === total }}
          onAnswered={(r) => {
            answered.current = [...answered.current, r]
            setResults(answered.current)
          }}
          onNext={() => (index + 1 < total ? setIndex(index + 1) : finish())}
        />
      ) : phase === 'review' && out.missed[reviewAt] ? (
        <Reviewed
          r={out.missed[reviewAt]}
          catalog={catalog}
          last={reviewAt + 1 === out.missed.length}
          onNext={() => (reviewAt + 1 < out.missed.length ? setReviewAt(reviewAt + 1) : setPhase('done'))}
        />
      ) : (
        <Panel>
          <p>
            <span className="text-title tabular-nums">{out.score}/{out.n}</span>
            <span className="ml-2 text-meta text-muted-foreground">{out.percent}%</span>
          </p>
          <ul className="space-y-1">
            {out.byTopic.map((t) => (
              <li key={t.topic} className="flex">
                <span className="flex-1">{t.title}</span>
                <span className="tabular-nums">
                  {t.score}/{t.n}
                </span>
              </li>
            ))}
          </ul>
          <div className="flex gap-stack">
            {out.missed.length > 0 && (
              <Button variant="outline" onClick={() => { setReviewAt(0); setPhase('review') }}>
                Review missed ({out.missed.length})
              </Button>
            )}
            <Button asChild>
              <Link to={back}>Done</Link>
            </Button>
          </div>
        </Panel>
      )}
    </section>
  )
}

// a missed question, read back: the learner's reply, the key and the detail
function Reviewed({ r, catalog, last, onNext }: { r: Result; catalog: Catalog; last: boolean; onNext: () => void }) {
  const course = catalog.courses.find((c) => c.slug === r.q.course)
  return (
    <div className="space-y-stack">
      <p className="text-meta text-muted-foreground">{questionHead(course, catalog.rules, r.q, '', false)}</p>
      <p className="text-heading whitespace-pre-wrap">{r.q.prompt}</p>
      {r.q.format === 'choice' && (
        <ul className="space-y-2">
          {r.order.map((i, pos) => (
            <li key={pos} className={cn('flex gap-3 rounded-xl border px-4 py-2.5', r.picked.includes(pos) && 'border-foreground bg-muted')}>
              <span className="font-medium">{LETTERS[pos]}</span>
              <span className="flex-1 whitespace-pre-wrap">{r.q.choices[i]}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="text-meta">{youLine(r)}</p>
      <Verdict r={r} />
      <Details r={r} course={course} />
      <Button onClick={onNext}>{last ? 'Back to results' : 'Next missed'}</Button>
    </div>
  )
}
