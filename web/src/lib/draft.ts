// the code a user typed on a problem and not yet submitted, kept per problem
// so the next sitting on it can find it. `at` is when it was typed: `flows.md`
// carries a draft only by when it was written. `sitting` is where it was
// typed, so a reload finds its own draft whatever the browser's clock says
export type Draft = { code: string; at: string; sitting: string }

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

export function keepDraft(problemId: string, sittingId: string, code: string): void {
  const draft: Draft = { code, at: new Date().toISOString(), sitting: sittingId }
  try {
    localStorage.setItem(key(problemId), JSON.stringify(draft))
  } catch {
    // a browser refusing storage costs the draft on reload, not the sitting
  }
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
