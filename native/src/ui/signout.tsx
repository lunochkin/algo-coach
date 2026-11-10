import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { Button, Dialog, Portal, Text } from 'react-native-paper';

import { SIGN_OUT, SIGN_OUT_TITLE, signOutWarning, STAY_SIGNED_IN } from '@algo-coach/core';
import { useStore } from '@/lib/store';

/**
 * Signing out sends the outbox first, and names the records it could not send
 * before deleting them: `knowledge.md`, A client's store.
 */
export function useSignOut(): { start: () => void; signing: boolean; dialog: ReactNode } {
  const st = useStore();
  const [signing, setSigning] = useState(false);
  const [unsent, setUnsent] = useState(0);

  const run = async (force: boolean) => {
    setUnsent(0);
    setSigning(true);
    try {
      const left = await st.signOut(force);
      if (left) setUnsent(left);
      else router.replace('/login');
    } finally {
      setSigning(false);
    }
  };

  const dialog = (
    <Portal>
      <Dialog visible={unsent > 0} onDismiss={() => setUnsent(0)}>
        <Dialog.Title>{SIGN_OUT_TITLE}</Dialog.Title>
        <Dialog.Content>
          <Text variant="bodyMedium">{signOutWarning(unsent, 'phone')}</Text>
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={() => setUnsent(0)}>{STAY_SIGNED_IN}</Button>
          <Button onPress={() => void run(true)}>{SIGN_OUT}</Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
  return { start: () => void run(false), signing, dialog };
}
