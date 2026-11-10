import { router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { appLine, type components } from '@algo-coach/core';
import { call } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { styles } from '@/ui/common';
import { useSignOut } from '@/ui/signout';

type SignedInApp = components['schemas']['SignedInApp'];

/**
 * Every app signed in as this account, as the web's account menu lists them.
 * This phone signs out from its own row, so its outbox is sent first; any
 * other app is revoked, and signed out at its next sync.
 */
export default function AppsScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useSignOut();
  const [apps, setApps] = useState<SignedInApp[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now] = useState(() => Date.now());

  const load = useCallback(async () => {
    try {
      const token = (await getToken()) ?? undefined;
      setApps((await (await call(st.settings.origin, '/apps', { token })).json()) as SignedInApp[]);
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }, [st.settings.origin]);

  useEffect(() => {
    void load();
  }, [load]);

  const revoke = async (app: SignedInApp) => {
    try {
      const token = (await getToken()) ?? undefined;
      await call(st.settings.origin, `/apps/${app.id}`, { token, method: 'DELETE' });
    } catch (e) {
      setError(String(e));
    }
    void load();
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Signed-in apps" />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          A revoked app is signed out at its next sync.
        </Text>
        {error ? (
          <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
            {error}
          </Text>
        ) : apps === null ? (
          <Text variant="bodyMedium">Reading the signed-in apps…</Text>
        ) : (
          apps.map((app) => (
            <Card key={app.id} mode="outlined">
              <Card.Content style={[styles.row, { gap: 12 }]}>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text variant="titleMedium">{app.current ? `${app.device} · this phone` : app.device}</Text>
                  <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                    {appLine(app, now)}
                  </Text>
                </View>
                {app.current ? (
                  <Button mode="outlined" icon="logout" disabled={signOut.signing} onPress={signOut.start}>
                    Sign out
                  </Button>
                ) : (
                  <Button mode="outlined" onPress={() => void revoke(app)} accessibilityLabel={`Revoke ${app.device}`}>
                    Revoke
                  </Button>
                )}
              </Card.Content>
            </Card>
          ))
        )}
      </ScrollView>
      {signOut.dialog}
    </View>
  );
}
