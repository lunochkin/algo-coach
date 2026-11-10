/** How long ago a day was, in whole days: today, yesterday, then days and months. */
export function lastAt(at: string | null | undefined, now: number): string {
  if (!at) return 'never';
  const days = Math.max(0, Math.floor((now - new Date(at).getTime()) / 86_400_000));
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 30) return `${days} days ago`;
  if (days < 365) return `${Math.floor(days / 30)} months ago`;
  return new Date(at).toLocaleDateString();
}

/** A signed-in app's line: when it was last used, and when it signed in. */
export function appLine(app: { last_used_at: string; created_at: string }, now: number): string {
  return `used ${lastAt(app.last_used_at, now)} · signed in ${lastAt(app.created_at, now)}`;
}
