import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { Appbar, Divider, Menu, Text, useTheme } from 'react-native-paper';

import {
  type components,
  named,
  NO_PROVIDER_LINKED,
  READING_SESSION,
  SETTINGS,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  YOUR_ACCOUNT,
} from '@algo-coach/core';
import { call } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useSignOut } from '@/ui/signout';

type Me = components['schemas']['Me'];

// who the token signs in as, read from the engine as the web's account menu reads it
export function useMe(read = true): Me | undefined {
  const { settings, hasToken } = useStore();
  const [me, setMe] = useState<Me | undefined>(undefined);
  useEffect(() => {
    if (!read || !hasToken) return;
    let live = true;
    void (async () => {
      try {
        const token = (await getToken()) ?? undefined;
        const body = (await (await call(settings.origin, '/me', { token })).json()) as Me;
        if (live) setMe(body);
      } catch {
        // offline: the name stays unread, and nothing else needs it
      }
    })();
    return () => {
      live = false;
    };
  }, [read, hasToken, settings.origin]);
  return me;
}

// the engine's own id under a verified address, or why there is no address
export function meLine(me: Me | undefined): string {
  if (me === undefined) return READING_SESSION;
  return me.email ? me.user_id : NO_PROVIDER_LINKED;
}

// Account sits apart from the sections, as the web's account menu does:
// `pages.md`, The structure
export function AccountMenu() {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const me = useMe(open);
  const signOut = useSignOut();
  return (
    <>
      <Menu
        visible={open}
        onDismiss={() => setOpen(false)}
        anchor={<Appbar.Action icon="account-circle-outline" onPress={() => setOpen(true)} accessibilityLabel={YOUR_ACCOUNT} />}>
        {/* text rather than items: a menu item holds one line, and the id runs longer */}
        <View style={{ paddingHorizontal: 16, paddingVertical: 8, maxWidth: 200, gap: 2 }}>
          <Text variant="titleSmall">{named(me)}</Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {meLine(me)}
          </Text>
        </View>
        <Divider />
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
