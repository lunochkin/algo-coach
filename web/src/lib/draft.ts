import { type Draft, draftKey, isDraft } from '@algo-coach/core'

// the draft in this browser's storage: core decides what a sitting opens on

export function draftOf(problemId: string): Draft | null {
  try {
    const raw = localStorage.getItem(draftKey(problemId))
    if (raw === null) return null
    const parsed: unknown = JSON.parse(raw)
    return isDraft(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function keepDraft(
  problemId: string,
  sittingId: string | null,
  code: string,
  restored = false,
): void {
  const draft: Draft = { code, at: new Date().toISOString(), sitting: sittingId, restored }
  try {
    localStorage.setItem(draftKey(problemId), JSON.stringify(draft))
  } catch {
    // a browser refusing storage costs the draft on reload, not the sitting
  }
}
