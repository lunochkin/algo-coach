/** One readable line for a sync error; the raw message stays available on tap. */
export function syncErrorSummary(error: string): string {
  if (/not signed in|signed out/i.test(error)) return 'Not signed in: sign in from Settings';
  if (/no engine address/i.test(error)) return 'No engine address: set one in Settings';
  if (/network request failed|timed? ?out|offline/i.test(error)) return 'Offline · retrying automatically';
  return 'Sync failed · retrying automatically';
}

/** How long ago a moment was, in the words a sync line reads. */
export function ago(iso: string, now: number): string {
  const s = Math.max(0, Math.round((now - Date.parse(iso)) / 1000));
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

/** The sync's state in one line: running, when it last finished, or never. */
export function syncLine(s: { running: boolean; lastAt: string | null }, now: number): string {
  return s.running ? 'Syncing…' : s.lastAt ? `Synced ${ago(s.lastAt, now)}` : 'Not synced yet';
}
