import { router } from 'expo-router';
import { useState } from 'react';
import { Appbar, Menu } from 'react-native-paper';

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
        anchor={<Appbar.Action icon="account-circle-outline" onPress={() => setOpen(true)} accessibilityLabel="Your account" />}>
        <Menu.Item
          leadingIcon="cog-outline"
          title="Settings"
          onPress={() => {
            setOpen(false);
            router.push('/settings');
          }}
        />
        <Menu.Item
          leadingIcon="cellphone-link"
          title="Signed-in apps"
          onPress={() => {
            setOpen(false);
            router.push('/apps');
          }}
        />
        <Menu.Item
          leadingIcon="logout"
          title="Sign out"
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
