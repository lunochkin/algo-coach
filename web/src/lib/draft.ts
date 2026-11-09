import type { Carry } from '@/api/client'

// the code a user typed on a problem and not yet submitted, kept per problem
// so the next sitting on it can find it. `at` is when it was typed: `flows.md`
// carries a draft only by when it was written. `sitting` is where it was
// typed, so a reload finds its own draft whatever the browser's clock says
// `restored` says the sitting restored an earlier solve, which its attempts
// then report
export type Draft = { code: string; at: string; sitting: string; restored?: boolean }

const key = (problemId: string) => `algo-coach:problem:${problemId}:draft`

export function draftOf(problemId: string): Draft | null {
  try {
    const raw = localStorage.getItem(key(problemId))
    if (raw === null) return null
    const parsed: unknown = JSON.parse(raw)
    return isDraft(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function keepDraft(
  problemId: string,
  sittingId: string,
  code: string,
  restored = false,
): void {
  const draft: Draft = { code, at: new Date().toISOString(), sitting: sittingId, restored }
  try {
    localStorage.setItem(key(problemId), JSON.stringify(draft))
  } catch {
    // a browser refusing storage costs the draft on reload, not the sitting
  }
}

// what a new sitting opens on, which `flows.md` gives: the newer of the
// draft and the last attempt's code, where each is work in progress. A draft
// from the solving sitting, or typed before the solve or the run, is an answer
// or an earlier run's work, and is left where it is
export function opening(draft: Draft | null, carry: Carry | null): string | null {
  const drafted =
    draft !== null &&
    draft.sitting !== carry?.solved_sitting_id &&
    (!carry?.solved_at || Date.parse(draft.at) > Date.parse(carry.solved_at)) &&
    (!carry?.run_started_at || Date.parse(draft.at) >= Date.parse(carry.run_started_at))
  const submitted =
    carry?.code != null && carry.at != null ? { code: carry.code, at: carry.at } : null
  if (!drafted) return submitted?.code ?? null
  if (submitted === null) return draft.code
  return Date.parse(draft.at) >= Date.parse(submitted.at) ? draft.code : submitted.code
}

function isDraft(value: unknown): value is Draft {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as Draft).code === 'string' &&
    typeof (value as Draft).at === 'string' &&
    typeof (value as Draft).sitting === 'string'
  )
}
