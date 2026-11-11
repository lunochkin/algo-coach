import { useEffect, useRef, useState } from 'react';

import { SIZE_SAVE_MS, sizeToSave } from '@algo-coach/core';

import { useStore } from './store';

/** The exam size field: saved as a record shortly after typing stops, and on leaving the screen. */
export function useSavedSize(): [string, (v: string) => void] {
  const st = useStore();
  const [size, setSize] = useState(String(st.examSize));
  const latest = useRef({ size, st });
  latest.current = { size, st };

  useEffect(() => {
    const t = setTimeout(() => save(latest.current), SIZE_SAVE_MS);
    return () => clearTimeout(t);
  }, [size]);
  useEffect(() => () => save(latest.current), []);

  return [size, setSize];
}

// a value equal to the standing one writes nothing, so a pause and a leave store one record
function save({ size, st }: { size: string; st: ReturnType<typeof useStore> }) {
  const n = sizeToSave(size, st.examSize);
  if (n !== null) void st.setSetting('exam_size', n);
}
