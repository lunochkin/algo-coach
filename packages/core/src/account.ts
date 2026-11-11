import { described, type EngineClient } from './engine';
import type { Outcome } from './sittingrun';
import { thisDevice, type ThisDevice } from './words/home';

/** How long ago a day was, in whole days: today, yesterday, then days and months. */
export function lastAt(at: string | null | undefined, now: number): string {
  if (!at) return 'never';
  const days = Math.max(0, Math.floor((now - new Date(at).getTime()) / 86_400_000));
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 30) return `${days} days ago`;
  if (days < 365) {
    const months = Math.floor(days / 30);
    return months === 1 ? 'a month ago' : `${months} months ago`;
  }
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

/** A device's title in the list, naming the device it is read on. */
export function deviceTitle(d: { kind: 'app' | 'browser'; name: string | null; current: boolean }, here: ThisDevice) {
  return d.current ? `${deviceName(d)} · ${thisDevice(here)}` : deviceName(d);
}

/** Revokes another device's sign-in. A refusal is named rather than read as revoked. */
export async function revokeDevice(
  client: EngineClient,
  d: { kind: 'app' | 'browser'; id: string },
): Promise<Outcome<null>> {
  try {
    const { error } = await client.DELETE('/api/devices/{kind}/{device_id}', {
      params: { path: { kind: d.kind, device_id: d.id } },
    });
    return error === undefined ? { ok: true, value: null } : { ok: false, refused: described(error) };
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}
