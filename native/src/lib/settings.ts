import * as SecureStore from 'expo-secure-store';

import { getMeta, setMeta } from './db';

export interface Settings {
  origin: string; // the engine the app syncs with, e.g. https://example.invalid
  device: string;
  newPerDay: number; // unseen questions a queue may introduce per day (04:00 rollover)
  examSize: number;
  courseOrder: string[]; // Home row order, by course slug; unknown slugs go last
  reminderHour: number;
}

export const DEFAULTS: Settings = {
  // the dev app talks to the local engine, which `just native-dev` reaches over USB;
  // the release app's engine comes from native/.env, which git ignores: the repo is public
  origin: __DEV__ ? 'http://localhost:8000' : (process.env.EXPO_PUBLIC_API_ORIGIN ?? ''),
  device: __DEV__ ? 'phone-dev' : 'phone', // the dev app must not write the release app's records
  newPerDay: 10,
  examSize: 40,
  courseOrder: [],
  reminderHour: 9,
};

// the engine's token for this app, never logged: `docs/architecture/README.md`
const TOKEN = 'app_token';

export async function loadSettings(): Promise<Settings> {
  const raw = await getMeta('settings');
  const saved = raw ? (JSON.parse(raw) as Partial<Settings>) : {};
  return { ...DEFAULTS, ...saved, origin: saved.origin || DEFAULTS.origin };
}

export async function saveSettings(s: Settings): Promise<void> {
  await setMeta('settings', JSON.stringify(s));
}

export function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN);
}

export async function setToken(token: string): Promise<void> {
  if (token) await SecureStore.setItemAsync(TOKEN, token);
  else await SecureStore.deleteItemAsync(TOKEN);
}
