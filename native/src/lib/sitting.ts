import {
  CLOCK_PREFERENCE_KEY,
  clockStartsItself,
  type Draft,
  draftKey,
  isDraft,
  preferenceAfter,
} from '@algo-coach/core';

import { getMeta, setMeta } from './db';

// the sitting's state the phone keeps itself, as the browser keeps it:
// `pages.md`. A draft is the user's code, so it is keyed to the signed-in
// user, and signing out deletes it with the rest of their copy

export const DRAFT_PREFIX = 'draft:';
const draftMeta = async (problemId: string) => `${DRAFT_PREFIX}${(await getMeta('user')) ?? ''}:${draftKey(problemId)}`;

export async function draftOf(problemId: string): Promise<Draft | null> {
  try {
    const raw = await getMeta(await draftMeta(problemId));
    if (raw === null) return null;
    const parsed: unknown = JSON.parse(raw);
    return isDraft(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export async function keepDraft(problemId: string, sittingId: string | null, code: string, restored = false) {
  const draft: Draft = { code, at: new Date().toISOString(), sitting: sittingId, restored };
  await setMeta(await draftMeta(problemId), JSON.stringify(draft));
}

export async function autoStarts(): Promise<boolean> {
  return clockStartsItself(await getMeta(CLOCK_PREFERENCE_KEY));
}

/** Set by the user's own press alone: a pause the app took going to the background says nothing. */
export async function pressed(to: 'start' | 'pause' | 'resume') {
  await setMeta(CLOCK_PREFERENCE_KEY, preferenceAfter(to));
}
