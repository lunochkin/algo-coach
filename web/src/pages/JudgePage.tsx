import {
  JUDGE_CLEAN,
  JUDGE_FLAWED,
  JUDGE_NEXT,
  JUDGE_NONE,
  JUDGE_NOTE,
  JUDGE_SUBMIT,
  JUDGE_TAP,
  JUDGE_TITLE,
  VERDICTS,
  judge,
  judgeDepth,
  judgeCorrection,
  judgeExample,
  nextJudged,
  separatingLines,
  verdictPassed,
} from '@climb/core'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'

import { api } from '@/api/client'
import type { components } from '@climb/core'
import { ErrorLine } from '@/components/ErrorLine'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { Tag } from '@/components/Tag'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type JudgedItem = components['schemas']['JudgedItem']
type JudgeDecided = components['schemas']['JudgeDecided']

// one item at a time: read, answer Correct or tap the wrong line, read the
// decision and its separating case, then Next. `pages.md`, Judging a solution
export function JudgePage() {
  const [params] = useSearchParams()
  const card = params.get('card')
  const [item, setItem] = useState<JudgedItem | null | undefined>(undefined)
  const [tapping, setTapping] = useState(false)
  const [tapped, setTapped] = useState<number | null>(null)
  const [decided, setDecided] = useState<JudgeDecided | null>(null)
  const [refused, setRefused] = useState<string | null>(null)

  const [round, setRound] = useState(0)

  useEffect(() => {
    let live = true
    void nextJudged(api, card).then((next) => {
      if (!live) return
      if (next.ok) setItem(next.value)
      else setRefused(next.refused)
    })
    return () => {
      live = false
    }
  }, [card, round])

  // Next clears the answer in the press itself, and the effect fetches
  function another() {
    setTapping(false)
    setTapped(null)
    setDecided(null)
    setRefused(null)
    setRound((one) => one + 1)
  }

  async function send(line: number | null) {
    if (!item) return
    const answered = await judge(api, item.item_id, line)
    if (answered.ok) setDecided(answered.value)
    else setRefused(answered.refused)
  }

  return (
    <section className="space-y-section">
      <PageHeader
        title={item ? item.template_title : JUDGE_TITLE}
        note={item ? item.card_title : JUDGE_NOTE}
      />
      {refused && <ErrorLine>{refused}</ErrorLine>}
      {item === null && <p className="text-meta text-muted-foreground">{JUDGE_NONE}</p>}
      {item && (
        <div className="space-y-stack">
          <div className="flex items-center gap-2">
            <Tag>{judgeDepth(item.depth)}</Tag>
          </div>
          <p className="text-meta text-muted-foreground">{item.asks}</p>
          <p className="font-mono text-meta">{judgeExample(item.example)}</p>
          <Panel className="overflow-hidden p-0">
            <ol className="font-mono text-sm">
              {item.lines.map((line, index) => {
                const number = index + 1
                const flawed = decided?.line === number
                return (
                  <li key={number}>
                    <button
                      type="button"
                      disabled={!tapping || decided !== null}
                      onClick={() => setTapped(number)}
                      className={cn(
                        'flex w-full gap-3 px-3 py-1 text-left disabled:cursor-default',
                        tapping && !decided && 'hover:bg-accent',
                        tapped === number && 'bg-accent',
                        flawed && 'border-l-4 border-verdict-wrong',
                      )}
                    >
                      <span className="w-6 shrink-0 text-right text-muted-foreground select-none">
                        {number}
                      </span>
                      <span className="whitespace-pre-wrap break-words">{line || ' '}</span>
                    </button>
                  </li>
                )
              })}
            </ol>
          </Panel>

          {!decided && !tapping && (
            <div className="flex flex-wrap gap-stack">
              <Button onClick={() => void send(null)}>{JUDGE_CLEAN}</Button>
              <Button variant="outline" onClick={() => setTapping(true)}>
                {JUDGE_FLAWED}
              </Button>
            </div>
          )}
          {!decided && tapping && (
            <div className="flex flex-wrap items-center gap-stack">
              <p className="text-meta text-muted-foreground">{JUDGE_TAP}</p>
              <Button disabled={tapped === null} onClick={() => void send(tapped)}>
                {JUDGE_SUBMIT}
              </Button>
            </div>
          )}

          {decided && (
            <Panel className="space-y-2">
              <p
                className={cn(
                  'font-medium',
                  verdictPassed(decided.verdict) ? 'text-verdict-passed' : 'text-verdict-wrong',
                )}
              >
                {VERDICTS[decided.verdict]}
              </p>
              {(() => {
                const fix = judgeCorrection(decided)
                return (
                  fix && (
                    <div>
                      <p className="text-meta text-muted-foreground">{fix.label}</p>
                      <pre className="font-mono text-sm whitespace-pre-wrap">{fix.code.trim()}</pre>
                    </div>
                  )
                )
              })()}
              {separatingLines(decided).map((line) => (
                <p key={line} className="font-mono text-meta">
                  {line}
                </p>
              ))}
              <Button onClick={another}>{JUDGE_NEXT}</Button>
            </Panel>
          )}
        </div>
      )}
    </section>
  )
}
