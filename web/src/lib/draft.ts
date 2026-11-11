import { type Draft, isDraft, isDraftKey, userDraftKey } from '@algo-coach/core'

// the draft in this browser's storage, keyed to its user: core decides what a
// sitting opens on

export function draftOf(user: string, problemId: string): Draft | null {
  try {
    const raw = localStorage.getItem(userDraftKey(user, problemId))
    if (raw === null) return null
    const parsed: unknown = JSON.parse(raw)
    return isDraft(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function keepDraft(
  user: string,
  problemId: string,
  sittingId: string | null,
  code: string,
  restored = false,
): void {
  const draft: Draft = { code, at: new Date().toISOString(), sitting: sittingId, restored }
  try {
    localStorage.setItem(userDraftKey(user, problemId), JSON.stringify(draft))
  } catch {
    // a browser refusing storage costs the draft on reload, not the sitting
  }
}

/** Signing out deletes every draft the browser holds, as it deletes the knowledge copy. */
export function eraseDrafts(): void {
  try {
    const keys = Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i))
    for (const key of keys) if (key !== null && isDraftKey(key)) localStorage.removeItem(key)
  } catch {
    // a browser refusing storage holds no draft to delete
  }
}
