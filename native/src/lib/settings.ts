import * as SecureStore from 'expo-secure-store';

import { getMeta, setMeta } from './db';

export interface Settings {
  origin: string; // the engine the app syncs with, e.g. https://example.invalid
  device: string;
  examSize: number;
  reminderHour: number;
}

export const DEFAULTS: Settings = {
  // the dev app talks to the local engine, which `just native-dev` reaches over USB;
  // the release app's engine comes from native/.env, which git ignores: the repo is public
  origin: __DEV__ ? 'http://localhost:8000' : (process.env.EXPO_PUBLIC_API_ORIGIN ?? ''),
  device: __DEV__ ? 'phone-dev' : 'phone', // the dev app must not write the release app's records
  examSize: 40,
  reminderHour: 9,
};

// the engine's token for this app, never logged: `docs/architecture/README.md`
const TOKEN = 'app_token';

export async function loadSettings(): Promise<Settings> {
  const raw = await getMeta('settings');
  const { newPerDay: _, courseOrder: __, ...saved } = raw ? (JSON.parse(raw) as Partial<Settings> & Legacy) : {};
  return { ...DEFAULTS, ...saved, origin: saved.origin || DEFAULTS.origin };
}

// kept on the device before the daily limit and the module order became records of the log
export interface Legacy {
  newPerDay?: number;
  courseOrder?: string[];
}

/** What an earlier build kept in the settings that the log holds now. */
export async function legacySettings(): Promise<Legacy> {
  const raw = await getMeta('settings');
  return raw ? (JSON.parse(raw) as Legacy) : {};
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
