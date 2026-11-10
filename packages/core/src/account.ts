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

/** A signed-in device's line: when it was last used, and when it signed in. */
export function deviceLine(d: { last_used_at: string; created_at: string }, now: number): string {
  return `used ${lastAt(d.last_used_at, now)} · signed in ${lastAt(d.created_at, now)}`;
}

const BROWSERS: [RegExp, string][] = [
  [/Edg\//, 'Edge'],
  [/Firefox\//, 'Firefox'],
  [/Chrome\//, 'Chrome'],
  [/Safari\//, 'Safari'],
];
const SYSTEMS: [RegExp, string][] = [
  [/Android/, 'Android'],
  [/iPhone|iPad/, 'iOS'],
  [/Mac OS X|Macintosh/, 'macOS'],
  [/Windows/, 'Windows'],
  [/Linux/, 'Linux'],
];

/** A device as a list names it: an app by its device name, a browser by its agent's browser and system. */
export function deviceName(d: { kind: 'app' | 'browser'; name: string | null }): string {
  if (d.kind === 'app') return d.name ?? 'An app';
  const agent = d.name ?? '';
  const browser = BROWSERS.find(([re]) => re.test(agent))?.[1];
  const system = SYSTEMS.find(([re]) => re.test(agent))?.[1];
  if (!browser) return 'A browser';
  return system ? `${browser} on ${system}` : browser;
}
