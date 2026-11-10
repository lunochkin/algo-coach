import { useEffect, useRef, useState } from 'react';

import { useStore } from './store';

type SizeKey = 'examSize';

export const validSize = (n: number) => Number.isInteger(n) && n >= 1 && n <= 500;

/** A size field bound to a setting: saved shortly after typing stops, and on leaving the screen. */
export function useSavedSize(key: SizeKey): [string, (v: string) => void] {
  const st = useStore();
  const [size, setSize] = useState(String(st.settings[key]));
  const latest = useRef({ size, st });
  latest.current = { size, st };

  useEffect(() => {
    const t = setTimeout(() => save(latest.current, key), 600);
    return () => clearTimeout(t);
  }, [size, key]);
  useEffect(() => () => save(latest.current, key), [key]);

  return [size, setSize];
}

function save({ size, st }: { size: string; st: ReturnType<typeof useStore> }, key: SizeKey) {
  const n = Number(size);
  if (validSize(n) && n !== st.settings[key]) void st.updateSettings({ ...st.settings, [key]: n });
}
