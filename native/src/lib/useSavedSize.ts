import { useEffect, useRef, useState } from 'react';

import { validSetting } from '@algo-coach/core';

import { useStore } from './store';

/** The exam size field: saved as a record shortly after typing stops, and on leaving the screen. */
export function useSavedSize(): [string, (v: string) => void] {
  const st = useStore();
  const [size, setSize] = useState(String(st.examSize));
  const latest = useRef({ size, st });
  latest.current = { size, st };

  useEffect(() => {
    const t = setTimeout(() => save(latest.current), 600);
    return () => clearTimeout(t);
  }, [size]);
  useEffect(() => () => save(latest.current), []);

  return [size, setSize];
}

// a value equal to the standing one writes nothing, so a pause and a leave store one record
function save({ size, st }: { size: string; st: ReturnType<typeof useStore> }) {
  const n = Number(size);
  if (validSetting('exam_size', n) && n !== st.examSize) void st.setSetting('exam_size', n);
}
