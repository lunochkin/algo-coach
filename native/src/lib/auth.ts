import * as Crypto from 'expo-crypto';
import * as WebBrowser from 'expo-web-browser';

import { call } from './engine';

// the engine redirects here, a constant on both sides: `docs/architecture/README.md`
export const REDIRECT = 'algocoach://signed-in';

export type Provider = 'google' | 'github';

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
export async function signIn(origin: string, provider: Provider, device: string): Promise<string> {
  const verifier = base64url(Crypto.getRandomBytes(48));
  const digest = await Crypto.digest(Crypto.CryptoDigestAlgorithm.SHA256, new TextEncoder().encode(verifier));
  const challenge = base64url(new Uint8Array(digest));
  const url = `${origin}/api/auth/${provider}?client=app&code_challenge=${challenge}`;
  const result = await WebBrowser.openAuthSessionAsync(url, REDIRECT);
  if (result.type !== 'success') throw new Error('sign-in cancelled');
  const query = new URL(result.url).searchParams;
  const refused = query.get('refused');
  if (refused) throw new Error(REFUSALS[refused] ?? `sign-in refused: ${refused}`);
  const code = query.get('code');
  if (!code) throw new Error('sign-in returned no code');
  const answer = await call(origin, '/auth/app/token', { body: { code, verifier, device } });
  return ((await answer.json()) as { token: string }).token;
}

export async function signOut(origin: string, token: string): Promise<void> {
  await call(origin, '/auth/app/signout', { token, method: 'POST', body: {} });
}

const REFUSALS: Record<string, string> = {
  uninvited: 'this email has no invitation',
  'no-email': 'the provider verified no email',
  incomplete: 'the sign-in did not complete',
};
