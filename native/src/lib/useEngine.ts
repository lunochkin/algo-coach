import { useCallback, useEffect, useState } from 'react';

import type { GetData, GetParams, GetPath } from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';

export interface Read<T> {
  data: T | null;
  error: string | null;
  reload: () => void;
}

/**
 * One GET from the engine, read at mount and on `reload`. Nothing is kept on
 * the device. A `path` of null reads nothing until it names one.
 */
export function useEngine<P extends GetPath>(
  path: P | null,
  ...params: [GetParams<P>] extends [never] ? [] : [GetParams<P>]
): Read<GetData<P>> {
  const { origin } = useStore().settings;
  const [data, setData] = useState<GetData<P> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  // the effect reads a path parameter by value: the caller builds a new object each render
  const named = JSON.stringify(params[0] ?? null);

  useEffect(() => {
    if (path === null) return;
    let live = true;
    void (async () => {
      try {
        const client = engine(origin, await getToken());
        const init = { params: { path: JSON.parse(named) as unknown } };
        const { data: body } = await client.GET(path, init as never);
        if (live) {
          setData(body as GetData<P>);
          setError(null);
        }
      } catch (e) {
        if (live) setError(String(e));
      }
    })();
    return () => {
      live = false;
    };
  }, [origin, path, named, tick]);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data, error, reload };
}
