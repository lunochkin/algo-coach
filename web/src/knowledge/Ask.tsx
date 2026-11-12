import { useEffect, useMemo, useReducer, useState } from 'react'

import {
  block,
  choiceOrder,
  detailSections,
  LETTERS,
  taughtBy,
  verdictView,
  yourAnswer,
  type Course,
  type Question,
  type Result,
  ASK_ANSWER,
  ASK_GUESSING,
  ASK_SAID_ELSE,
  ASK_SAID_TRAP,
  ASK_TICK_RECALLED,
  ASK_TRAPS,
  askChoose,
  detailAccepted,
  DETAIL_NONE,
  DETAIL_YOU,
  DETAIL_YOUR_ANSWER,
  DETAIL_YOURS,
  detailsToggle,
  askAct,
  askReducer,
  askResult,
  initialAsk,
  keyPointLabel,
} from '@algo-coach/core'

import { Link } from 'react-router'

import { SectionHeading } from '@/components/SectionHeading'
import { PlainCode, PythonCode } from '@/components/PythonCode'
import { optionTile } from '@/components/optionTile'
import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLearner } from '@/knowledge/learner'
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
  // opens an answer's lesson over the queue, which following its link would end
  onLesson?: (course: string, slug: string, anchor: string) => void
}

// one question, one act at a time: the answer, then the verdict and Next.
// `pages.md`, The knowledge pages
export function Ask({ q, course, head, onAnswered, onNext, exam, onLesson }: Props) {
  // shuffled on each display, so a position carries no answer
  const order = useMemo(() => choiceOrder(q.choices.length), [q])
  // the answer's state and its one press, as core keeps them for every platform
  const [state, dispatch] = useReducer(askReducer, undefined, initialAsk)
  const { picked, text, guessing, revealed, recalled, fell, wrong, result } = state
  const [details, setDetails] = useState(false)
  const multi = q.answer.length > 1
  const press = askAct(q, state, exam ?? null)

  // an exam moves on at once; elsewhere the verdict reads before Next
  function act() {
    if (press.act === 'next') return onNext()
    if (press.act === 'reveal') return dispatch({ type: 'reveal' })
    if (!press.enabled) return
    const r = askResult(q, order, state)
    onAnswered(r)
    if (exam) onNext()
    else dispatch({ type: 'answered', result: r })
  }
  const toggle = (pos: number) => dispatch({ type: 'pick', pos, multi })

  // a digit picks an option, and Enter submits or moves on: a reader at a
  // keyboard answers faster than by pointer
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (
        event.target instanceof HTMLInputElement ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey
      )
        return
      const pos = Number(event.key) - 1
      if (!result && q.format === 'choice' && pos >= 0 && pos < order.length) {
        event.preventDefault()
        toggle(pos)
      } else if (event.key === 'Enter') {
        event.preventDefault()
        act()
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
          {multi && <p className="text-meta text-muted-foreground">{askChoose(q.answer.length)}</p>}
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
                className={cn(optionTile(on), 'w-full items-baseline')}
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
            if (press.act === 'submit') act()
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
            onChange={(event) => dispatch({ type: 'text', text: event.target.value })}
          />
        </form>
      )}

      {q.format !== 'card' && !result && (
        <div className="flex items-center gap-2">
          <Checkbox
            id="guessing"
            checked={guessing}
            onCheckedChange={(on) => dispatch({ type: 'guess', on: on === true })}
          />
          <Label htmlFor="guessing">{ASK_GUESSING}</Label>
        </div>
      )}

      {q.format === 'card' && revealed && (
        <div className="space-y-2">
          <p className="font-medium">{ASK_TICK_RECALLED}</p>
          {q.key.map((point, i) => (
            <Tick
              key={i}
              label={keyPointLabel(i, block(point))}
              on={recalled.has(i)}
              disabled={!!result}
              onFlip={() => dispatch({ type: 'recall', i })}
            />
          ))}
          {q.traps.length > 0 && <p className="pt-2 font-medium">{ASK_TRAPS}</p>}
          {q.traps.map((trap, i) => (
            <Tick
              key={i}
              label={block(trap)}
              hint={ASK_SAID_TRAP}
              on={fell.has(i)}
              disabled={!!result}
              onFlip={() => dispatch({ type: 'fall', i })}
            />
          ))}
          <Tick
            label={ASK_SAID_ELSE}
            on={wrong}
            disabled={!!result}
            onFlip={() => dispatch({ type: 'wrong' })}
          />
        </div>
      )}

      {result && <Verdict r={result} />}
      {result && (
        <div className="space-y-stack">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDetails(!details)}
            aria-expanded={details}
          >
            {detailsToggle(details)}
          </Button>
          {details && <Details r={result} course={course} onLesson={onLesson} />}
        </div>
      )}

      <div>
        <Button disabled={!press.enabled} onClick={act}>
          {press.label}
        </Button>
      </div>
    </div>
  )
}

function Tick(props: {
  label: string
  hint?: string
  on: boolean
  disabled: boolean
  onFlip: () => void
}) {
  return (
    <label
      // one option tile, as a choice is drawn: picked reads bordered and tinted
      className={cn(optionTile(props.on), 'items-start')}
    >
      <Checkbox
        checked={props.on}
        disabled={props.disabled}
        onCheckedChange={props.onFlip}
        className="mt-1"
      />
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
        <p
          className={cn('font-medium', head.correct ? 'text-verdict-passed' : 'text-verdict-wrong')}
        >
          {head.text}
        </p>
      )}
      {explain && <p className="whitespace-pre-wrap">{explain}</p>}
      {note && <p className="text-meta text-muted-foreground">{note}</p>}
    </div>
  )
}

export function Details({
  r,
  course,
  onLesson,
}: {
  r: Result
  course: Course | undefined
  onLesson?: (course: string, slug: string, anchor: string) => void
}) {
  const answer = yourAnswer(r)
  const sections = detailSections(r.q)
  const { catalog } = useLearner()
  const lessons = taughtBy(r.q, course, catalog?.lessonsDone)
  return (
    <Panel>
      {answer && (
        <Section title={DETAIL_YOUR_ANSWER}>
          {answer.kind === 'rows' ? (
            answer.rows.map((row) => (
              <div key={row.key} className={cn('rounded-md px-2 py-1', row.yours && 'bg-muted')}>
                <p className="whitespace-pre-wrap">
                  <span className={row.ok ? 'text-verdict-passed' : 'text-verdict-wrong'}>
                    {row.mark}{' '}
                  </span>
                  {row.label}
                  {row.yours && <span className="text-muted-foreground">{DETAIL_YOURS}</span>}
                </p>
                {row.note && (
                  <p className="pl-4 text-meta whitespace-pre-wrap text-muted-foreground">
                    {row.note}
                  </p>
                )}
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
            <PlainCode>{x.code}</PlainCode>
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
          {onLesson ? (
            <button
              type="button"
              onClick={() => onLesson(x.course, x.slug, x.anchor)}
              className="font-medium underline-offset-4 hover:underline"
            >
              {x.label}
            </button>
          ) : (
            <Link
              to={lessonPath(x.course, x.slug, x.anchor)}
              className="font-medium underline-offset-4 hover:underline"
            >
              {x.label}
            </Link>
          )}
        </p>
      ))}
    </Panel>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1">
      <SectionHeading sub title={title} />
      {children}
    </section>
  )
}
