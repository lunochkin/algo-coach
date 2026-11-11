import { useEffect, useRef, useState } from 'react';
import { RefreshControl } from 'react-native';
import { useTheme } from 'react-native-paper';

import { useStore } from '@/lib/store';

/**
 * Pulling a screen down syncs the knowledge log and reads the screen's engine
 * data again. The spinner stops once the sync reports, refused or not.
 */
export function usePullSync(...reloads: (() => void)[]) {
  const st = useStore();
  const theme = useTheme();
  const [pulled, setPulled] = useState(false);
  const before = useRef(st.sync);

  useEffect(() => {
    if (pulled && st.sync !== before.current && !st.sync.running) setPulled(false);
  }, [pulled, st.sync]);
  // a sync that never reports leaves no spinner behind
  useEffect(() => {
    if (!pulled) return;
    const t = setTimeout(() => setPulled(false), 15_000);
    return () => clearTimeout(t);
  }, [pulled]);

  const onRefresh = () => {
    before.current = st.sync;
    setPulled(true);
    for (const reload of reloads) reload();
    st.requestSync(0);
  };
  return (
    <RefreshControl
      refreshing={pulled}
      onRefresh={onRefresh}
      colors={[theme.colors.primary]}
      progressBackgroundColor={theme.colors.elevation.level2}
    />
  );
}
