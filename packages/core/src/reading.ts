import { loadingLine, readFailure } from './practice';

// the four readings of a page, decided once for both clients: `pages.md`,
// A page's areas. A failure needs a message, so an empty one reads as none

export type PageReading<T> =
  | { kind: 'failed'; line: string }
  | { kind: 'loading'; line: string }
  | { kind: 'blank'; line: string }
  | { kind: 'content'; data: T };

export function pageReading<T>(
  of: string,
  state: { data?: T | null; error?: string | null },
  blank?: string,
  blankWhen: (data: T) => boolean = (data) => Array.isArray(data) && data.length === 0,
): PageReading<T> {
  if (state.error) return { kind: 'failed', line: readFailure(of, state.error) };
  if (state.data === undefined || state.data === null) return { kind: 'loading', line: loadingLine(of) };
  if (blank !== undefined && blankWhen(state.data)) return { kind: 'blank', line: blank };
  return { kind: 'content', data: state.data };
}

/** The device's copy as a reading: held once ready, failed with the sync while it holds nothing. */
export function copyReading<T>(ready: boolean, syncError: string | null, data: T | null | undefined) {
  const shown = ready ? data : undefined;
  return { data: shown, error: shown == null && syncError ? syncError : null };
}
