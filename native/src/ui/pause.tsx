import { useState, type ReactNode } from 'react';
import { Button, Dialog, Portal, Text } from 'react-native-paper';

import type { Course } from '@algo-coach/core';
import { useStore } from '@/lib/store';

const SCOPE = 'Continue, exams across all courses, the due/weak totals and reminders';

/** Confirmed pause/resume of a course; returns the trigger and the dialog to render. */
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
        <Dialog.Title>{`${pausing ? 'Pause' : 'Resume'} ${target?.title ?? ''}?`}</Dialog.Title>
        <Dialog.Content>
          <Text variant="bodyMedium">
            {pausing
              ? `It will be left out of ${SCOPE}. Its module screen still starts a filtered queue on it.`
              : `It will be back in ${SCOPE}.`}
          </Text>
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={close}>Cancel</Button>
          <Button onPress={confirm}>{pausing ? 'Pause' : 'Resume'}</Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
  return { ask: setTarget, dialog };
}

/** Confirmed archive of a course: hidden everywhere, progress kept, restorable in Settings. */
export function useArchive(): { ask: (c: Course) => void; dialog: ReactNode } {
  const st = useStore();
  const [target, setTarget] = useState<Course | null>(null);
  const close = () => setTarget(null);
  const dialog = (
    <Portal>
      <Dialog visible={!!target} onDismiss={close}>
        <Dialog.Title>{`Archive ${target?.title ?? ''}?`}</Dialog.Title>
        <Dialog.Content>
          <Text variant="bodyMedium">
            It disappears from the app; your progress is kept. Restore it in Settings.
          </Text>
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={close}>Cancel</Button>
          <Button
            onPress={() => {
              if (target) void st.setCourseStatus(target.slug, 'archived');
              close();
            }}>
            Archive
          </Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
  return { ask: setTarget, dialog };
}
