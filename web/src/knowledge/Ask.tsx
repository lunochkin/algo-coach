import { useEffect, useMemo, useState } from 'react'

import {
  block,
  cardFields,
  cardLabel,
  choiceOrder,
  detailSections,
  gradeChoice,
  hasAnswer,
  LETTERS,
  matchShort,
  splitGuess,
  taughtBy,
  verdictView,
  yourAnswer,
  type Course,
  type Question,
  type Result,
  ASK_ANSWER,
  ASK_GUESSING,
  ASK_NEXT,
  ASK_REVEAL,
  ASK_SAID_ELSE,
  ASK_SAID_TRAP,
  ASK_TICK_RECALLED,
  ASK_TRAPS,
  askChoose,
  askSubmit,
  detailAccepted,
  DETAIL_NONE,
  DETAIL_YOU,
  DETAIL_YOUR_ANSWER,
  DETAIL_YOURS,
  detailsToggle,
} from '@algo-coach/core'

import { Link } from 'react-router'

import { PythonCode } from '@/components/PythonCode'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { lessonPath } from '@/knowledge/paths'
import { cn } from '@/lib/utils'

type Props = {
  q: Question
  course: Course | undefined
  head: string // the line naming where the question sits and why it is served
  onAnswered: (r: Result) => void
  onNext: () => void
  // an exam shows no verdict until its end: the answer moves on at once
  exam?: { last: boolean }
}

// one question, one act at a time: the answer, then the verdict and Next.
// `pages.md`, The knowledge pages
export function Ask({ q, course, head, onAnswered, onNext, exam }: Props) {
  // shuffled on each display, so a position carries no answer
  const order = useMemo(() => choiceOrder(q.choices.length), [q])
  const [picked, setPicked] = useState<number[]>([])
  const [text, setText] = useState('')
  const [guessing, setGuessing] = useState(false)
  const [revealed, setRevealed] = useState(false)
  const [recalled, setRecalled] = useState<Set<number>>(new Set())
  const [fell, setFell] = useState<Set<number>>(new Set())
  const [wrong, setWrong] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [details, setDetails] = useState(false)
  const multi = q.answer.length > 1
  const canSubmit = q.format === 'short' ? hasAnswer(text) : picked.length > 0

  function answer(r: Result) {
    onAnswered(r)
    if (exam) onNext()
    else setResult(r)
  }

  function submit() {
    if (q.format === 'short') {
      const [reply, suffix] = splitGuess(text)
      answer({ q, correct: matchShort(reply, q), guess: guessing || suffix, order, picked: [], reply })
    } else {
      answer({ q, correct: gradeChoice(q, order, picked), guess: guessing, order, picked, reply: '' })
    }
  }

  function grade() {
    const card = cardFields(q.key.length, recalled, fell, wrong)
    answer({ q, correct: card.grade === 'k', guess: false, order, picked: [], reply: '', grade: card.grade, card })
  }

  function toggle(pos: number) {
    if (!multi) setPicked([pos])
    else setPicked(picked.includes(pos) ? picked.filter((p) => p !== pos) : [...picked, pos])
  }

  // a digit picks an option, and Enter submits or moves on: a reader at a
  // keyboard answers faster than by pointer
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement || event.metaKey || event.ctrlKey || event.altKey) return
      const pos = Number(event.key) - 1
      if (!result && q.format === 'choice' && pos >= 0 && pos < order.length) {
        event.preventDefault()
        toggle(pos)
      } else if (event.key === 'Enter') {
        event.preventDefault()
        if (result) onNext()
        else if (q.format === 'card') {
          if (revealed) grade()
          else setRevealed(true)
        } else if (canSubmit) submit()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  return (
    <div className="space-y-stack">
      <p className="text-meta text-muted-foreground">{head}</p>
      <p className="text-heading whitespace-pre-wrap">{block(q.prompt)}</p>
      {q.code && <PythonCode code={q.code} />}

      {q.format === 'choice' && (
        <div className="space-y-2" role={multi ? 'group' : 'radiogroup'}>
          {multi && <p className="text-meta text-brand-deep">{askChoose(q.answer.length)}</p>}
          {order.map((i, pos) => {
            const on = picked.includes(pos)
            return (
              <button
                key={pos}
                type="button"
                role={multi ? 'checkbox' : 'radio'}
                aria-checked={on}
                disabled={!!result}
                onClick={() => toggle(pos)}
                className={cn(
                  'flex w-full items-baseline gap-3 rounded-xl border px-4 py-2.5 text-left',
                  on ? 'border-foreground bg-muted' : 'hover:bg-muted/50',
                )}
              >
                <span className="font-medium">{LETTERS[pos]}</span>
                <span className="flex-1 whitespace-pre-wrap">{q.choices[i]}</span>
                <span className="text-meta text-muted-foreground">{pos + 1}</span>
              </button>
            )
          })}
        </div>
      )}

      {q.format === 'short' && (
        <form
          onSubmit={(event) => {
            event.preventDefault()
            if (canSubmit && !result) submit()
          }}
        >
          <Input
            aria-label={ASK_ANSWER}
            autoFocus
            autoComplete="off"
            spellCheck={false}
            className="font-mono"
            value={text}
            disabled={!!result}
            onChange={(event) => setText(event.target.value)}
          />
        </form>
      )}

      {q.format !== 'card' && !result && (
        <div className="flex items-center gap-2">
          <Checkbox id="guessing" checked={guessing} onCheckedChange={(on) => setGuessing(on === true)} />
          <Label htmlFor="guessing">{ASK_GUESSING}</Label>
        </div>
      )}

      {q.format === 'card' && revealed && (
        <div className="space-y-2">
          <p className="font-medium">{ASK_TICK_RECALLED}</p>
          {q.key.map((point, i) => (
            <Tick key={i} label={`${i + 1}. ${block(point)}`} on={recalled.has(i)} disabled={!!result} onFlip={() => setRecalled(flip(recalled, i))} />
          ))}
          {q.traps.length > 0 && <p className="pt-2 font-medium">{ASK_TRAPS}</p>}
          {q.traps.map((trap, i) => (
            <Tick key={i} label={block(trap)} hint={ASK_SAID_TRAP} on={fell.has(i)} disabled={!!result} onFlip={() => setFell(flip(fell, i))} />
          ))}
          <Tick label={ASK_SAID_ELSE} on={wrong} disabled={!!result} onFlip={() => setWrong(!wrong)} />
        </div>
      )}

      {result && <Verdict r={result} />}
      {result && (
        <div className="space-y-stack">
          <Button variant="ghost" size="sm" onClick={() => setDetails(!details)} aria-expanded={details}>
            {detailsToggle(details)}
          </Button>
          {details && <Details r={result} course={course} />}
        </div>
      )}

      <div>
        {result ? (
          <Button onClick={onNext}>{ASK_NEXT}</Button>
        ) : q.format === 'card' ? (
          revealed ? (
            <Button onClick={grade}>{cardLabel(q.key.length, recalled, fell, wrong)}</Button>
          ) : (
            <Button onClick={() => setRevealed(true)}>{ASK_REVEAL}</Button>
          )
        ) : (
          <Button disabled={!canSubmit} onClick={submit}>
            {askSubmit(!!exam, !!exam?.last)}
          </Button>
        )}
      </div>
    </div>
  )
}

function flip(s: Set<number>, i: number): Set<number> {
  const next = new Set(s)
  if (next.has(i)) next.delete(i)
  else next.add(i)
  return next
}

function Tick(props: { label: string; hint?: string; on: boolean; disabled: boolean; onFlip: () => void }) {
  return (
    <label className={cn('flex items-start gap-3 rounded-xl border px-4 py-2.5', props.on && 'bg-muted')}>
      <Checkbox checked={props.on} disabled={props.disabled} onCheckedChange={props.onFlip} className="mt-1" />
      <span className="flex-1">
        <span className="whitespace-pre-wrap">{props.label}</span>
        {props.hint && <span className="block text-meta text-muted-foreground">{props.hint}</span>}
      </span>
    </label>
  )
}

export function Verdict({ r }: { r: Result }) {
  const { head, explain, note } = verdictView(r)
  return (
    <div className="space-y-1">
      {head && (
        <p className={cn('font-medium', head.correct ? 'text-verdict-passed' : 'text-verdict-wrong')}>{head.text}</p>
      )}
      {explain && <p className="whitespace-pre-wrap">{explain}</p>}
      {note && <p className="text-meta text-muted-foreground">{note}</p>}
    </div>
  )
}

export function Details({ r, course }: { r: Result; course: Course | undefined }) {
  const answer = yourAnswer(r)
  const sections = detailSections(r.q)
  const lessons = taughtBy(r.q, course)
  return (
    <div className="space-y-stack rounded-xl border bg-card px-4 py-3">
      {answer && (
        <Section title={DETAIL_YOUR_ANSWER}>
          {answer.kind === 'rows' ? (
            answer.rows.map((row) => (
              <div key={row.key} className={cn('rounded-md px-2 py-1', row.yours && 'bg-muted')}>
                <p className="whitespace-pre-wrap">
                  <span className={row.ok ? 'text-verdict-passed' : 'text-verdict-wrong'}>{row.mark} </span>
                  {row.label}
                  {row.yours && <span className="text-muted-foreground">{DETAIL_YOURS}</span>}
                </p>
                {row.note && <p className="pl-4 text-meta whitespace-pre-wrap text-muted-foreground">{row.note}</p>}
              </div>
            ))
          ) : (
            <p>
              {DETAIL_YOU} <span className="font-mono">{answer.you}</span>
              <span className="text-muted-foreground">{detailAccepted(answer.accepted)}</span>
            </p>
          )}
        </Section>
      )}
      {sections.map((x) => (
        <Section key={x.title} title={x.title}>
          {'code' in x ? (
            <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">{x.code}</pre>
          ) : 'items' in x ? (
            <ul className="list-disc space-y-1 pl-5">
              {x.items.map((item, i) => (
                <li key={i} className="whitespace-pre-wrap">
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="whitespace-pre-wrap">{x.text}</p>
          )}
        </Section>
      ))}
      {!answer && sections.length === 0 && (
        <p className="text-meta text-muted-foreground">{DETAIL_NONE}</p>
      )}
      {lessons.map((x) => (
        <p key={x.slug} className="text-meta">
          <Link to={lessonPath(x.course, x.slug, x.anchor)} className="underline underline-offset-2">
            {x.label}
          </Link>
        </p>
      ))}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1">
      <h3 className="text-meta font-medium text-brand-deep">{title}</h3>
      {children}
    </section>
  )
}
