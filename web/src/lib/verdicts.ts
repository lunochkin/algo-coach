import { failures, OUTCOME_LABELS, SEVEREST } from '@algo-coach/core'

import type { CaseResult } from '@/api/client'

export { failures, SEVEREST }

// one token per outcome, beside the label core gives it: `pages.md` gives why
// a wrong answer and a timeout are not one colour
export const OUTCOME = {
  passed: { label: OUTCOME_LABELS.passed, mark: 'bg-verdict-passed', text: 'text-verdict-passed' },
  wrong: { label: OUTCOME_LABELS.wrong, mark: 'bg-verdict-wrong', text: 'text-verdict-wrong' },
  timeout: {
    label: OUTCOME_LABELS.timeout,
    mark: 'bg-verdict-timeout',
    text: 'text-verdict-timeout',
  },
  crashed: {
    label: OUTCOME_LABELS.crashed,
    mark: 'bg-verdict-crashed',
    text: 'text-verdict-crashed',
  },
} as const

export type Outcome = keyof typeof OUTCOME

export function severest(results: CaseResult[]): Outcome | undefined {
  return SEVEREST.find((outcome) => results.some((one) => one.outcome === outcome))
}
