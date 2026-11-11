import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { Button } from 'react-native-paper';

import { SIGN_OUT, SIGN_OUT_TITLE, signOutWarning, STAY_SIGNED_IN } from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { Sheet } from '@/ui/sheet';

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
    <Sheet
      visible={unsent > 0}
      onDismiss={() => setUnsent(0)}
      title={SIGN_OUT_TITLE}
      note={signOutWarning(unsent, 'phone')}
      actions={
        <>
          <Button onPress={() => setUnsent(0)}>{STAY_SIGNED_IN}</Button>
          <Button mode="contained" onPress={() => void run(true)}>
            {SIGN_OUT}
          </Button>
        </>
      }
    />
  );
  return { start: () => void run(false), signing, dialog };
}
