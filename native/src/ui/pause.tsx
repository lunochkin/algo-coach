import { useState, type ReactNode } from 'react';
import { Button } from 'react-native-paper';

import { ARCHIVE_BODY, ARCHIVE_KEEP, archiveTitle, type Course, MODULE_ARCHIVE } from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { Sheet } from '@/ui/sheet';

/** Confirmed archive of a module: hidden everywhere, progress kept, restorable in Settings. */
export function useArchive(onArchived: () => void): { ask: (c: Course) => void; dialog: ReactNode } {
  const st = useStore();
  const [target, setTarget] = useState<Course | null>(null);
  const close = () => setTarget(null);
  const dialog = (
    <Sheet
      visible={!!target}
      onDismiss={close}
      title={archiveTitle(target?.title ?? '')}
      note={ARCHIVE_BODY}
      actions={
        <>
          <Button onPress={close}>{ARCHIVE_KEEP}</Button>
          <Button
            mode="contained"
            onPress={() => {
              if (!target) return;
              void st.setCourseStatus(target.slug, 'archived');
              close();
              onArchived();
            }}
          >
            {MODULE_ARCHIVE}
          </Button>
        </>
      }
    />
  );
  return { ask: setTarget, dialog };
}
