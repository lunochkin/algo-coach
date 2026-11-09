/** One readable line for a sync error; the raw message stays available on tap. */
export function syncErrorSummary(error: string): string {
  if (/not signed in|signed out/i.test(error)) return 'Not signed in: sign in from Settings';
  if (/no engine address/i.test(error)) return 'No engine address: set one in Settings';
  if (/network request failed|timed? ?out|offline/i.test(error)) return 'Offline · retrying automatically';
  return 'Sync failed · retrying automatically';
}
