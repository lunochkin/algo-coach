import { useState, type ReactNode } from 'react';
import { Button, Dialog, Portal, Text } from 'react-native-paper';

import { ARCHIVE_BODY, ARCHIVE_KEEP, archiveTitle, type Course, MODULE_ARCHIVE } from '@algo-coach/core';
import { useStore } from '@/lib/store';

/** Confirmed archive of a module: hidden everywhere, progress kept, restorable in Settings. */
export function useArchive(onArchived: () => void): { ask: (c: Course) => void; dialog: ReactNode } {
  const st = useStore();
  const [target, setTarget] = useState<Course | null>(null);
  const close = () => setTarget(null);
  const dialog = (
    <Portal>
      <Dialog visible={!!target} onDismiss={close}>
        <Dialog.Title>{archiveTitle(target?.title ?? '')}</Dialog.Title>
        <Dialog.Content>
          <Text variant="bodyMedium">{ARCHIVE_BODY}</Text>
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={close}>{ARCHIVE_KEEP}</Button>
          <Button
            onPress={() => {
              if (!target) return;
              void st.setCourseStatus(target.slug, 'archived');
              close();
              onArchived();
            }}>
            {MODULE_ARCHIVE}
          </Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
  return { ask: setTarget, dialog };
}
