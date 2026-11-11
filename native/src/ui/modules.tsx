import { router } from 'expo-router';
import type { ReactNode } from 'react';

import { type ModuleRow as Row, moduleStats, PAUSED, QUESTIONS_PASSED } from '@algo-coach/core';
import { PickRow } from '@/ui/rows';

/**
 * One module reads as one row wherever it is listed, the knowledge home and
 * the Practice tab alike: `pages.md`, A page's areas. A press opens the module.
 */
export function ModuleRow({ row, aside, onLongPress }: { row: Row; aside?: ReactNode; onLongPress?: () => void }) {
  return (
    <PickRow
      title={row.c.title}
      badge={row.c.paused ? PAUSED : null}
      stats={moduleStats(row.toReview, row.total)}
      note={[row.view.title, row.view.detail].filter(Boolean).join(' · ')}
      progress={{ value: row.passed, total: row.total, label: QUESTIONS_PASSED }}
      onPress={() => router.push({ pathname: '/module', params: { course: row.c.slug } })}
      onLongPress={onLongPress}
      aside={aside}
    />
  );
}
