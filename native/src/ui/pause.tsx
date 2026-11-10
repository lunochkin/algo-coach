import { useState, type ReactNode } from 'react';
import { Button, Dialog, Portal, Text } from 'react-native-paper';

import { ARCHIVE_BODY, ARCHIVE_KEEP, archiveTitle, type Course, MODULE_ARCHIVE, MODULE_PAUSE, MODULE_RESUME } from '@algo-coach/core';
import { useStore } from '@/lib/store';

const SCOPE = 'Continue, exams across all modules, the due/weak totals and reminders';

/** Confirmed pause/resume of a module; returns the trigger and the dialog to render. */
export function usePauseToggle(): { ask: (c: Course) => void; dialog: ReactNode } {
  const st = useStore();
  const [target, setTarget] = useState<Course | null>(null);
  const close = () => setTarget(null);
  const confirm = () => {
    if (!target) return;
    void st.setCourseStatus(target.slug, target.paused ? 'active' : 'paused');
    close();
  };
  const pausing = !target?.paused;
  const dialog = (
    <Portal>
      <Dialog visible={!!target} onDismiss={close}>
        <Dialog.Title>{`${pausing ? MODULE_PAUSE : MODULE_RESUME} ${target?.title ?? ''}?`}</Dialog.Title>
        <Dialog.Content>
          <Text variant="bodyMedium">
            {pausing
              ? `It will be left out of ${SCOPE}. Its module screen still starts a filtered queue on it.`
              : `It will be back in ${SCOPE}.`}
          </Text>
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={close}>Cancel</Button>
          <Button onPress={confirm}>{pausing ? MODULE_PAUSE : MODULE_RESUME}</Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
  return { ask: setTarget, dialog };
}

/** Confirmed archive of a module: hidden everywhere, progress kept, restorable in Settings. */
export function useArchive(): { ask: (c: Course) => void; dialog: ReactNode } {
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
              if (target) void st.setCourseStatus(target.slug, 'archived');
              close();
            }}>
            {MODULE_ARCHIVE}
          </Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
  return { ask: setTarget, dialog };
}
