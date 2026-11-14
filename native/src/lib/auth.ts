import * as Crypto from 'expo-crypto';
import * as WebBrowser from 'expo-web-browser';

import { type components, refusal, SIGN_IN_CANCELLED, SIGN_IN_NO_CODE } from '@climb/core';

import { call, engine } from './engine';

// the engine redirects here, a constant on both sides: `docs/architecture/README.md`.
// The dev app has a scheme of its own, so the release app never receives its code
export const REDIRECT = __DEV__ ? 'climbancedev://signed-in' : 'climbance://signed-in';
const CLIENT = __DEV__ ? 'app-dev' : 'app';

// `dev` is the local engine's dev login, which signs the dev app alone in
export type Provider = components['schemas']['Provider'] | 'dev';
export type Offered = components['schemas']['Offered'];

// what this build may sign in through, of what the engine names: the dev app
// the dev login alone, the release app the providers alone
export async function offered(origin: string): Promise<Offered> {
  const { data } = await engine(origin).GET('/api/sign-in');
  const named = data as Offered;
  return __DEV__ ? { providers: [], dev_login: named.dev_login } : { providers: named.providers, dev_login: null };
}

const base64url = (bytes: Uint8Array) =>
  btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

/**
 * The provider's sign-in in a browser sheet, then the code it returns exchanged
 * for the app's token. PKCE binds the code to this app: another app claiming the
 * scheme receives the code without the verifier.
 */
export async function signIn(
  origin: string,
  provider: Provider,
  device: string,
): Promise<{ token: string; user: string }> {
  const verifier = base64url(Crypto.getRandomBytes(48));
  const digest = await Crypto.digest(Crypto.CryptoDigestAlgorithm.SHA256, new TextEncoder().encode(verifier));
  const challenge = base64url(new Uint8Array(digest));
  const url = `${origin}/api/auth/${provider}?client=${CLIENT}&code_challenge=${challenge}`;
  const result = await WebBrowser.openAuthSessionAsync(url, REDIRECT);
  if (result.type !== 'success') throw new Error(SIGN_IN_CANCELLED);
  const query = new URL(result.url).searchParams;
  const refused = query.get('refused');
  if (refused) throw new Error(refusal(refused));
  const code = query.get('code');
  if (!code) throw new Error(SIGN_IN_NO_CODE);
  const answer = await call(origin, '/auth/app/token', { body: { code, verifier, device } });
  const issued = (await answer.json()) as { token: string; user_id: string };
  return { token: issued.token, user: issued.user_id };
}

export async function signOut(origin: string, token: string): Promise<void> {
  await call(origin, '/auth/app/signout', { token, method: 'POST', body: {} });
}
