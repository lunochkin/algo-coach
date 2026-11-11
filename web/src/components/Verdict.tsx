import { useState } from 'react'

import {
  FAILURE_ARGS,
  FAILURE_ERROR,
  FAILURE_EXPECTED,
  FAILURE_RETURNED,
  submissionView,
  type SubmissionView,
} from '@algo-coach/core'

import type { CaseResult, Submitted } from '@/api/client'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { OUTCOME } from '@/lib/verdicts'

export function Verdict({ submitted }: { submitted: Submitted }) {
  const view = submissionView(submitted)

  return (
    <div className="space-y-stack">
      <p className={cn('font-medium', view.overall && OUTCOME[view.overall].text)}>
        {view.verdict}
      </p>
      {view.failures && <p className="text-meta text-muted-foreground">{view.failures}</p>}
      <CaseStrip results={submitted.verification.results ?? []} />
      {view.failure && <FailureView failure={view.failure} />}
    </div>
  )
}

// one mark per case, in the order the problem carries them
export function CaseStrip({ results }: { results: CaseResult[] }) {
  return (
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
  )
}

function FailureView({ failure }: { failure: NonNullable<SubmissionView['failure']> }) {
  return (
    <div className="space-y-2 rounded-md border p-3 text-meta">
      <p className={cn('font-medium', OUTCOME[failure.outcome].text)}>{failure.title}</p>
      <Value label={FAILURE_ARGS} value={failure.args} />
      <Value label={FAILURE_EXPECTED} value={failure.expected} />
      {failure.outcome === 'wrong' && <Value label={FAILURE_RETURNED} value={failure.returned} />}
      {failure.error && <Value label={FAILURE_ERROR} text={failure.error} />}
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
      {/* a word breaks only where it alone overflows the line: a traceback keeps
          its words, and a long value without spaces still wraps */}
      <pre className="max-h-64 overflow-auto rounded bg-muted p-2 font-mono text-code whitespace-pre-wrap break-words">
        {cut ? `${full.slice(0, SHOWN)}…` : full}
      </pre>
    </div>
  )
}
