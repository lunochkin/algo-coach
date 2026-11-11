import { X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import {
  block,
  type Catalog,
  ExamRun,
  type ExamRecords,
  certExam,
  examOpening,
  type ExamPlan,
  examPool,
  LETTERS,
  levelExam,
  levelExamLabel,
  levelName,
  levels,
  questionHead,
  type Result,
  setting,
  type SettingRecord,
  validSetting,
  youLine,
  EXAM_ALL,
  EXAM_DONE,
  EXAM_LEVEL,
  EXAM_MODULE,
  EXAM_NOTE,
  EXAM_SIZE,
  EXAM_TITLE,
  examReviewMissed,
  examReviewNext,
  QUEUE_STOP,
  examModuleChoice,
  newRecord,
  certExamRule,
  CERT_EXAM_MISSING,
  CERT_EXAM_START,
  BACK_CERTIFICATIONS,
  BACK_KNOWLEDGE,
  OF,
} from '@algo-coach/core'

import { Choice } from '@/components/Choice'
import { PickPanel, PickRow } from '@/components/PickRow'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Ask, Details, Verdict } from '@/knowledge/Ask'
import { linesOf, loadedFrom, useKnowledge, type Knowledge } from '@/knowledge/context'
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

  const catalog = learner.catalog
  if (plan && catalog)
    return <Running plan={plan} catalog={catalog} back={cert ? CERTIFICATIONS : KNOWLEDGE} />
  const certified = cert ? catalog?.courses.map((c) => c.certs?.get(cert)).find(Boolean) : undefined
  return (
    <section className="space-y-section">
      <PageHeader
        back={
          cert
            ? { to: CERTIFICATIONS, label: BACK_CERTIFICATIONS }
            : { to: KNOWLEDGE, label: BACK_KNOWLEDGE }
        }
        title={certified?.title ?? EXAM_TITLE}
        note={EXAM_NOTE}
      />
      <Loaded of={OF.exam} state={loadedFrom(k, catalog ?? undefined)}>
        {(catalog) =>
          cert ? (
            <CertChoice id={cert} catalog={catalog} onStart={setPlan} />
          ) : (
            <LevelChoice catalog={catalog} onStart={setPlan} />
          )
        }
      </Loaded>
    </section>
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
    const t = setTimeout(() => void k.add('setting', newRecord.setting('exam_size', n)), 600)
    return () => clearTimeout(t)
  }, [n, stored, k])

  return (
    <section className="space-y-section">
      <div className="space-y-stack">
        <Choice label={EXAM_MODULE}>
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            className="w-auto flex-wrap"
            value={course ?? ALL}
            onValueChange={(v) => v && setCourse(v === ALL ? null : v)}
          >
            <ToggleGroupItem value={ALL}>{EXAM_ALL}</ToggleGroupItem>
            {catalog.courses.map((c) => (
              <ToggleGroupItem key={c.slug} value={c.slug}>
                {examModuleChoice(c)}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </Choice>
        <Choice label={EXAM_LEVEL}>
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            className="w-auto flex-wrap"
            value={String(level)}
            onValueChange={(v) => v && setLevel(Number(v))}
          >
            {levels(catalog.rules).map((l) => (
              <ToggleGroupItem key={l} value={String(l)}>
                {levelName(catalog.rules, l)}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
          <p className="text-meta text-muted-foreground">{catalog.rules.levels[level] ?? ''}</p>
        </Choice>
        <div className="flex items-center gap-stack">
          <Label htmlFor="exam-size">{EXAM_SIZE}</Label>
          <Input
            id="exam-size"
            inputMode="numeric"
            className="w-24 tabular-nums"
            value={size}
            aria-invalid={!validSetting('exam_size', n)}
            onChange={(e) => setSize(e.target.value)}
          />
        </div>
        <Button
          disabled={!b || !count}
          onClick={() => {
            if (!b) return
            // a size typed just before the press is saved with the start, not lost to the timer
            if (n !== stored) void k.add('setting', newRecord.setting('exam_size', n))
            onStart(levelExam(b, level, n))
          }}
        >
          {levelExamLabel(catalog.rules, level, pool, count)}
        </Button>
      </div>
    </section>
  )
}

function CertChoice({
  id,
  catalog,
  onStart,
}: {
  id: string
  catalog: Catalog
  onStart: (p: ExamPlan) => void
}) {
  const { board } = useLearner()
  const c = catalog.courses.find((x) => x.certs?.get(id))
  const x = c?.certs?.get(id)
  const b = c ? board(c.slug) : null
  return (
    <section className="space-y-section">
      {c && x && b ? (
        <Panel>
          <p>{certExamRule(x.rule.size, x.rule.passShare)}</p>
          <div>
            <Button
              onClick={() => {
                const p = certExam(b, c, id)
                if (p) onStart(p)
              }}
            >
              {CERT_EXAM_START}
            </Button>
          </div>
        </Panel>
      ) : (
        <p className="text-meta text-muted-foreground">{CERT_EXAM_MISSING}</p>
      )}
    </section>
  )
}

function Running({ plan, catalog, back }: { plan: ExamPlan; catalog: Catalog; back: string }) {
  const k = useKnowledge()
  const [run] = useState(() => new ExamRun(plan, catalog.courses))
  const [, rerender] = useState(0)
  const out = run.outcome

  // leaving through the navigation ends the exam the same way; a closed tab
  // leaves no record. The cleanup reads the latest `add`
  const latest = useRef(k)
  useEffect(() => {
    latest.current = k
  })
  useEffect(() => () => store(latest.current.add, run.end()), [run])

  function act(step: () => ExamRecords | null | void) {
    store(k.add, step() ?? null)
    rerender((n) => n + 1)
  }

  const q = run.question
  const course = q ? catalog.courses.find((c) => c.slug === q.course) : undefined
  const reviewed = run.reviewed

  return (
    <section className="space-y-section">
      <PageHeader
        title={run.title}
        aside={
          run.phase === 'ask' ? (
            <Button variant="outline" size="sm" onClick={() => act(() => run.stop())}>
              <X />
              {QUEUE_STOP}
            </Button>
          ) : (
            <span className="text-meta tabular-nums">
              {out.score}/{out.n}
            </span>
          )
        }
      />

      {q ? (
        <Ask
          key={run.index}
          q={q}
          course={course}
          head={questionHead(course, catalog.rules, q, '', false)}
          exam={{ last: run.last }}
          onAnswered={(r) => act(() => run.answer(r))}
          onNext={() => act(() => run.next())}
        />
      ) : reviewed ? (
        <Reviewed
          r={reviewed}
          catalog={catalog}
          last={run.reviewLast}
          onNext={() => act(() => run.nextMissed())}
        />
      ) : (
        <Panel>
          <p>
            <span className="text-title tabular-nums">
              {out.score}/{out.n}
            </span>
            <span className="ml-2 text-meta text-muted-foreground">{out.percent}%</span>
          </p>
          <PickPanel>
            {out.byTopic.map((t) => (
              <PickRow
                key={t.topic}
                title={t.title}
                stats={[{ label: '', value: `${t.score}/${t.n}` }]}
              />
            ))}
          </PickPanel>
          <div className="flex gap-stack">
            {out.missed.length > 0 && (
              <Button variant="outline" onClick={() => act(() => run.review())}>
                {examReviewMissed(out.missed.length)}
              </Button>
            )}
            <Button asChild>
              <Link to={back}>{EXAM_DONE}</Link>
            </Button>
          </div>
        </Panel>
      )}
    </section>
  )
}

// the answers, the stint and a certification's record are stored together at the end
function store(add: Knowledge['add'], records: ExamRecords | null) {
  if (!records) return
  for (const a of records.attempts) void add('attempt', a)
  void add('session', records.session)
  if (records.cert) void add('cert', records.cert)
}

// a missed question, read back: the learner's reply, the key and the detail
function Reviewed({
  r,
  catalog,
  last,
  onNext,
}: {
  r: Result
  catalog: Catalog
  last: boolean
  onNext: () => void
}) {
  const course = catalog.courses.find((c) => c.slug === r.q.course)
  return (
    <div className="space-y-stack">
      <p className="text-meta text-muted-foreground">
        {questionHead(course, catalog.rules, r.q, '', false)}
      </p>
      <p className="text-heading whitespace-pre-wrap">{block(r.q.prompt)}</p>
      {r.q.format === 'choice' && (
        <ul className="space-y-2">
          {r.order.map((i, pos) => (
            <li
              key={pos}
              className={cn(
                'flex gap-3 rounded-xl border px-4 py-2.5',
                r.picked.includes(pos) && 'border-foreground bg-muted',
              )}
            >
              <span className="font-medium">{LETTERS[pos]}</span>
              <span className="flex-1 whitespace-pre-wrap">{r.q.choices[i]}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="text-meta">{youLine(r)}</p>
      <Verdict r={r} />
      <Details r={r} course={course} />
      <Button onClick={onNext}>{examReviewNext(last)}</Button>
    </div>
  )
}
