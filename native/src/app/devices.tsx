import { router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  DEVICES_LOADING,
  deviceLine,
  deviceName,
  readFailure,
  REVOKE,
  REVOKED_NOTE,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  thisDevice,
  type components,
} from '@algo-coach/core';
import { call, described } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { Failed, styles } from '@/ui/common';
import { useSignOut } from '@/ui/signout';

type SignedInDevice = components['schemas']['SignedInDevice'];

/**
 * Every browser and app signed in as this account, as the web's account menu
 * lists them. This phone signs out from its own row, so its outbox is sent
 * first; any other device is revoked, and signed out at its next request.
 */
export default function DevicesScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useSignOut();
  const [devices, setDevices] = useState<SignedInDevice[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // a refused revoke, read beside the list as the web reads it
  const [failed, setFailed] = useState<string | null>(null);
  const [now] = useState(() => Date.now());

  const load = useCallback(async () => {
    try {
      const token = (await getToken()) ?? undefined;
      setDevices((await (await call(st.settings.origin, '/devices', { token })).json()) as SignedInDevice[]);
      setError(null);
    } catch (e) {
      setError(readFailure('the signed-in devices', described(e)));
    }
  }, [st.settings.origin]);

  useEffect(() => {
    void load();
  }, [load]);

  const revoke = async (device: SignedInDevice) => {
    setFailed(null);
    try {
      const token = (await getToken()) ?? undefined;
      await call(st.settings.origin, `/devices/${device.kind}/${device.id}`, { token, method: 'DELETE' });
    } catch (e) {
      setFailed(described(e));
    }
    void load();
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={SIGNED_IN_DEVICES} />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {REVOKED_NOTE}
        </Text>
        {error ? (
          <Failed message={error} onRetry={() => void load()} />
        ) : devices === null ? (
          <Text variant="bodyMedium">{DEVICES_LOADING}</Text>
        ) : (
          devices.map((device) => (
            <Card key={device.id} mode="outlined">
              <Card.Content style={[styles.row, { gap: 12 }]}>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text variant="titleMedium">
                    {device.current ? `${deviceName(device)} · ${thisDevice('phone')}` : deviceName(device)}
                  </Text>
                  <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                    {deviceLine(device, now)}
                  </Text>
                </View>
                {device.current ? (
                  <Button mode="outlined" icon="logout" disabled={signOut.signing} onPress={signOut.start}>
                    {SIGN_OUT}
                  </Button>
                ) : (
                  <Button
                    mode="outlined"
                    onPress={() => void revoke(device)}
                    accessibilityLabel={`Revoke ${deviceName(device)}`}
                  >
                    {REVOKE}
                  </Button>
                )}
              </Card.Content>
            </Card>
          ))
        )}
        {failed ? (
          <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
            {failed}
          </Text>
        ) : null}
      </ScrollView>
      {signOut.dialog}
    </View>
  );
}
