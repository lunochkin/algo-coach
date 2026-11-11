import { useCallback, useEffect, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  deviceLine,
  deviceName,
  REVOKE,
  REVOKED_NOTE,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  type components,
  OF,
  revokeLabel,
  deviceTitle,
  revokeDevice,
} from '@algo-coach/core';
import { described, engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { ErrorLine, Loaded, styles, ScreenHeader } from '@/ui/common';
import { PickPanel, PickRow } from '@/ui/rows';
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
      const { data } = await engine(st.settings.origin, await getToken()).GET('/api/devices');
      setDevices(data ?? []);
      setError(null);
    } catch (e) {
      setError(described(e));
    }
  }, [st.settings.origin]);

  useEffect(() => {
    void load();
  }, [load]);

  const revoke = async (device: SignedInDevice) => {
    setFailed(null);
    const revoked = await revokeDevice(engine(st.settings.origin, await getToken()), device);
    if (!revoked.ok) setFailed(revoked.refused);
    void load();
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={SIGNED_IN_DEVICES} />
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {REVOKED_NOTE}
        </Text>
        <Loaded of={OF.devices} state={{ data: devices, error, reload: () => void load() }}>
          {(listed) => (
            <PickPanel>
              {listed.map((device) => (
                <PickRow
                  key={device.id}
                  title={deviceTitle(device, 'phone')}
                  stats={[]}
                  note={deviceLine(device, now)}
                  aside={
                    device.current ? (
                      <Button mode="outlined" icon="logout" disabled={signOut.signing} onPress={signOut.start}>
                        {SIGN_OUT}
                      </Button>
                    ) : (
                      <Button
                        mode="outlined"
                        icon="close"
                        onPress={() => void revoke(device)}
                        accessibilityLabel={revokeLabel(deviceName(device))}
                      >
                        {REVOKE}
                      </Button>
                    )
                  }
                />
              ))}
            </PickPanel>
          )}
        </Loaded>
        {failed ? <ErrorLine>{failed}</ErrorLine> : null}
      </ScrollView>
      {signOut.dialog}
    </View>
  );
}
