import { useCallback, useEffect, useState } from 'react';

import { call } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';

export interface Read<T> {
  data: T | null;
  error: string | null;
  reload: () => void;
}

/** One GET from the engine, read at mount and on `reload`. Nothing is kept on the device. */
export function useEngine<T>(path: string): Read<T> {
  const { origin } = useStore().settings;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let live = true;
    void (async () => {
      try {
        const token = (await getToken()) ?? undefined;
        const body = (await (await call(origin, path, { token })).json()) as T;
        if (live) {
          setData(body);
          setError(null);
        }
      } catch (e) {
        if (live) setError(String(e));
      }
    })();
    return () => {
      live = false;
    };
  }, [origin, path, tick]);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data, error, reload };
}
