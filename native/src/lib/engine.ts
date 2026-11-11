/** The engine's HTTP API, as the app calls it. */
import { engineClient, type EngineClient } from '@algo-coach/core';

export { described } from '@algo-coach/core';

export class SignedOut extends Error {}

export class EngineError extends Error {
  constructor(
    readonly status: number,
    message: string,
    // the API refuses with the domain's own sentence, as the web reads it
    readonly detail: string | null = null,
  ) {
    super(message);
  }
}

function detailOf(body: string): string | null {
  try {
    const parsed: unknown = JSON.parse(body);
    if (parsed && typeof parsed === 'object' && 'detail' in parsed) return String(parsed.detail);
  } catch {
    // not JSON: the status line carries it
  }
  return null;
}

const signedOut = () => new SignedOut('signed out: sign in again in Settings');

async function refused(path: string, response: Response): Promise<never> {
  if (response.status === 401) throw signedOut();
  const body = await response.text();
  throw new EngineError(response.status, `${path} ${response.status}: ${body}`, detailOf(body));
}

const noOrigin = () => new EngineError(0, 'no engine address: set one in Settings');

/** The typed client: a refusal throws, `SignedOut` on a 401, and a 304 is answered. */
export function engine(origin: string, token?: string | null): EngineClient {
  if (!origin) throw noOrigin();
  const client = engineClient(origin, {
    token: () => token,
    signedOut: () => {
      throw signedOut();
    },
  });
  client.use({
    async onResponse({ request, response }) {
      // a 401 reaches `signedOut`, which runs after this
      if (!response.ok && response.status !== 304 && response.status !== 401) {
        await refused(new URL(request.url).pathname.replace(/^\/api/, ''), response);
      }
    },
  });
  return client;
}

// the routes the API's schema does not name: the app's own sign-in exchange
export async function call(
  origin: string,
  path: string,
  init: { token?: string; method?: string; body?: unknown } = {},
): Promise<Response> {
  if (!origin) throw noOrigin();
  const headers: Record<string, string> = {};
  if (init.token) headers.authorization = `Bearer ${init.token}`;
  if (init.body !== undefined) headers['content-type'] = 'application/json';
  const response = await fetch(`${origin}/api${path}`, {
    method: init.method ?? (init.body === undefined ? 'GET' : 'POST'),
    headers,
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (!response.ok) await refused(path, response);
  return response;
}
