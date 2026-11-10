/** The engine's HTTP API, as the app calls it. */

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

export function described(e: unknown): string {
  if (e instanceof EngineError && e.detail) return e.detail;
  return e instanceof Error ? e.message : String(e);
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

export async function call(
  origin: string,
  path: string,
  init: { token?: string; method?: string; body?: unknown; headers?: Record<string, string> } = {},
): Promise<Response> {
  if (!origin) throw new EngineError(0, 'no engine address: set one in Settings');
  const headers: Record<string, string> = { ...init.headers };
  if (init.token) headers.authorization = `Bearer ${init.token}`;
  if (init.body !== undefined) headers['content-type'] = 'application/json';
  const response = await fetch(`${origin}/api${path}`, {
    method: init.method ?? (init.body === undefined ? 'GET' : 'POST'),
    headers,
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (response.status === 401) throw new SignedOut('signed out: sign in again in Settings');
  if (!response.ok && response.status !== 304) {
    const body = await response.text();
    throw new EngineError(response.status, `${path} ${response.status}: ${body}`, detailOf(body));
  }
  return response;
}
