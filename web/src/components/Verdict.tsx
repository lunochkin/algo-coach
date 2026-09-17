import { useState } from 'react'

import type { Failure, Submitted } from '@/api/client'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const OUTCOME = {
  passed: { label: 'passed', mark: 'bg-verdict-passed', text: 'text-verdict-passed' },
  wrong: { label: 'wrong answer', mark: 'bg-verdict-wrong', text: 'text-verdict-wrong' },
  timeout: { label: 'timed out', mark: 'bg-verdict-timeout', text: 'text-verdict-timeout' },
  crashed: { label: 'crashed', mark: 'bg-verdict-crashed', text: 'text-verdict-crashed' },
} as const

type Outcome = keyof typeof OUTCOME

// the order `corpus.md` folds a run by: a solution that only ran slowly is
// otherwise correct, which is a different remedy from one answering wrongly
const SEVEREST: Outcome[] = ['crashed', 'wrong', 'timeout', 'passed']

export function Verdict({ submitted }: { submitted: Submitted }) {
  const results = submitted.verification.results ?? []
  const passed = results.filter((one) => one.outcome === 'passed').length
  // the run reads as its severest case, so the line and the strip agree
  const overall = SEVEREST.find((outcome) => results.some((one) => one.outcome === outcome))

  return (
    <div className="space-y-3">
      <p className={cn('font-medium', overall && OUTCOME[overall].text)}>
        {submitted.attempt.solved ? 'Solved' : 'Not solved'}: {passed} of {results.length} cases
        passed
      </p>
      <ol className="flex flex-wrap gap-1" aria-label="Cases, in order">
        {results.map((one, index) => (
          <li
            key={one.case_id}
            title={`case ${index + 1}: ${OUTCOME[one.outcome].label}${
              one.elapsed_ms == null ? '' : `, ${one.elapsed_ms} ms`
            }`}
            className={cn('size-3 rounded-sm', OUTCOME[one.outcome].mark)}
          />
        ))}
      </ol>
      {submitted.failure && (
        <FailureView failure={submitted.failure} index={indexOf(submitted)} />
      )}
    </div>
  )
}

function FailureView({ failure, index }: { failure: Failure; index: number }) {
  return (
    <div className="space-y-2 rounded-md border p-3 text-sm">
      <p className={cn('font-medium', OUTCOME[failure.outcome].text)}>
        Case {index + 1}: {OUTCOME[failure.outcome].label}
      </p>
      <Value label="Arguments" value={failure.args} />
      <Value label="Expected" value={failure.expected} />
      {failure.outcome === 'wrong' && <Value label="Returned" value={failure.returned} />}
      {failure.error && <Value label="Error" text={failure.error} />}
    </div>
  )
}

// cut on screen past this many characters: a separating case weighs up to a
// mebibyte, and drawing it whole stalls the page. The response stays whole
const SHOWN = 2_000

function Value({ label, value, text }: { label: string; value?: unknown; text?: string }) {
  const [whole, setWhole] = useState(false)
  const full = text ?? JSON.stringify(value)
  const cut = !whole && full.length > SHOWN

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">{label}</span>
        {full.length > SHOWN && (
          <>
            <Button variant="ghost" size="xs" onClick={() => setWhole(!whole)}>
              {whole ? 'Cut' : `Show all ${(full.length / 1024).toFixed(0)} KB`}
            </Button>
            <Button variant="ghost" size="xs" onClick={() => navigator.clipboard.writeText(full)}>
              Copy
            </Button>
          </>
        )}
      </div>
      <pre className="max-h-64 overflow-auto rounded bg-muted p-2 font-mono text-xs whitespace-pre-wrap break-all">
        {cut ? `${full.slice(0, SHOWN)}…` : full}
      </pre>
    </div>
  )
}

function indexOf(submitted: Submitted): number {
  const results = submitted.verification.results ?? []
  return results.findIndex((one) => one.case_id === submitted.failure?.case_id)
}
