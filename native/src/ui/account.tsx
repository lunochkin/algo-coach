import { router } from 'expo-router';
import { useState } from 'react';
import { Appbar, Menu } from 'react-native-paper';

import { SETTINGS, SIGN_OUT, SIGNED_IN_DEVICES, YOUR_ACCOUNT } from '@algo-coach/core';
import { useSignOut } from '@/ui/signout';

// Account sits apart from the sections, as the web's account menu does:
// `pages.md`, The structure
export function AccountMenu() {
  const [open, setOpen] = useState(false);
  const signOut = useSignOut();
  return (
    <>
      <Menu
        visible={open}
        onDismiss={() => setOpen(false)}
        anchor={<Appbar.Action icon="account-circle-outline" onPress={() => setOpen(true)} accessibilityLabel={YOUR_ACCOUNT} />}>
        <Menu.Item
          leadingIcon="cog-outline"
          title={SETTINGS}
          onPress={() => {
            setOpen(false);
            router.push('/settings');
          }}
        />
        <Menu.Item
          leadingIcon="cellphone-link"
          title={SIGNED_IN_DEVICES}
          onPress={() => {
            setOpen(false);
            router.push('/devices');
          }}
        />
        <Menu.Item
          leadingIcon="logout"
          title={SIGN_OUT}
          disabled={signOut.signing}
          onPress={() => {
            setOpen(false);
            signOut.start();
          }}
        />
      </Menu>
      {signOut.dialog}
    </>
  );
}
