import { describe, expect, it } from 'vitest';

import { described, engineClient } from './engine';

function recording(status = 200, body: string | null = '[]') {
  const seen: Request[] = [];
  const fetch = async (request: Request) => {
    seen.push(request);
    return new Response(body, { status, headers: { 'content-type': 'application/json' } });
  };
  return { seen, fetch };
}

describe('engineClient', () => {
  it('sends the token as a bearer header', async () => {
    const { seen, fetch } = recording();
    await engineClient('https://engine.test', { token: async () => 'tok-1', fetch }).GET('/api/devices');
    expect(seen[0]?.headers.get('authorization')).toBe('Bearer tok-1');
  });

  it('sends no authorization where no token is given', async () => {
    const { seen, fetch } = recording();
    await engineClient('https://engine.test', { fetch }).GET('/api/devices');
    expect(seen[0]?.headers.get('authorization')).toBeNull();
  });

  it('encodes a path parameter', async () => {
    const { seen, fetch } = recording(204, null);
    await engineClient('https://engine.test', { fetch }).DELETE('/api/devices/{kind}/{device_id}', {
      params: { path: { kind: 'app', device_id: 'a/b c' } },
    });
    expect(new URL(seen[0]!.url).pathname).toBe('/api/devices/app/a%2Fb%20c');
  });

  it('calls signedOut on a 401 alone', async () => {
    const refused: number[] = [];
    const signedOut = (r: Response) => void refused.push(r.status);
    await engineClient('https://engine.test', { fetch: recording(401, '{}').fetch, signedOut }).GET('/api/me');
    await engineClient('https://engine.test', { fetch: recording(403, '{}').fetch, signedOut }).GET('/api/me');
    expect(refused).toEqual([401]);
  });
});

describe('described', () => {
  it("reads the API's detail first", () => {
    expect(described({ detail: 'no such card' })).toBe('no such card');
    expect(described(Object.assign(new Error('500'), { detail: 'refused' }))).toBe('refused');
  });

  it('reads an error by its message and a string as itself', () => {
    expect(described(new Error('offline'))).toBe('offline');
    expect(described('Bad Gateway')).toBe('Bad Gateway');
  });

  it('writes any other value as JSON', () => {
    expect(described({ code: 1 })).toBe('{"code":1}');
    expect(described(undefined)).toBe('undefined');
  });
});
