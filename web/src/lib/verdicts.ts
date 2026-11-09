import type { CaseResult } from '@/api/client'

// one token per outcome, and the label a reader sees: `pages.md` gives why a
// wrong answer and a timeout are not one colour
export const OUTCOME = {
  passed: { label: 'passed', mark: 'bg-verdict-passed', text: 'text-verdict-passed' },
  wrong: { label: 'wrong answer', mark: 'bg-verdict-wrong', text: 'text-verdict-wrong' },
  timeout: { label: 'timed out', mark: 'bg-verdict-timeout', text: 'text-verdict-timeout' },
  crashed: { label: 'crashed', mark: 'bg-verdict-crashed', text: 'text-verdict-crashed' },
} as const

export type Outcome = keyof typeof OUTCOME

// the order `corpus.md` folds a run by: a solution that only ran slowly is
// otherwise correct, which is a different remedy from one answering wrongly
export const SEVEREST: Outcome[] = ['crashed', 'wrong', 'timeout', 'passed']

export function severest(results: CaseResult[]): Outcome | undefined {
  return SEVEREST.find((outcome) => results.some((one) => one.outcome === outcome))
}

// the mix of failures in words, since the strip carries it in colour alone
export function failures(results: CaseResult[]): string[] {
  return SEVEREST.filter((outcome) => outcome !== 'passed')
    .map((outcome) => [outcome, results.filter((one) => one.outcome === outcome).length] as const)
    .filter(([, count]) => count > 0)
    .map(([outcome, count]) => `${count} ${OUTCOME[outcome].label}`)
}
