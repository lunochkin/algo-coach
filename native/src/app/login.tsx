import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { Button, HelperText, Text, TextInput, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { signIn, type Provider } from '@/lib/auth';
import { APP_NAME } from '@/lib/name';
import { useStore } from '@/lib/store';

const ADDRESS = /^https?:\/\/[^\s/]+$/;
const LABELS = { google: 'Continue with Google', github: 'Continue with GitHub', dev: 'Continue with the dev login' };
const ICONS = { google: 'google', github: 'github', dev: 'laptop' };

/** The app's first screen until it holds a token: sign in through a provider. */
export default function LoginScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [signing, setSigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // asked only where the build named no engine: native/.env normally does
  const [origin, setOrigin] = useState(st.settings.origin);
  const originOk = ADDRESS.test(origin.trim());

  const signInWith = async (provider: Provider) => {
    setSigning(true);
    setError(null);
    try {
      if (origin.trim() !== st.settings.origin) {
        await st.updateSettings({ ...st.settings, origin: origin.trim() });
      }
      await st.updateToken(await signIn(origin.trim(), provider, st.settings.device));
      st.requestSync(0);
      router.replace('/');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSigning(false);
    }
  };

  return (
    <View
      style={{
        flex: 1,
        justifyContent: 'center',
        gap: 16,
        padding: 24,
        paddingTop: insets.top + 24,
        paddingBottom: insets.bottom + 24,
        backgroundColor: theme.colors.background,
      }}>
      <Text variant="displaySmall">{APP_NAME}</Text>
      <Text variant="bodyLarge">
        {__DEV__ ? 'The dev app syncs with the local engine.' : 'Sign in to sync your practice with the engine.'}
      </Text>
      {!st.settings.origin ? (
        <>
          <TextInput
            mode="outlined"
            label="Engine address"
            value={origin}
            onChangeText={setOrigin}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          {!originOk ? <HelperText type="error">An address such as https://example.invalid</HelperText> : null}
        </>
      ) : null}
      {(__DEV__ ? (['dev'] as const) : (['google', 'github'] as const)).map((provider) => (
        <Button
          key={provider}
          mode="contained"
          icon={ICONS[provider]}
          loading={signing}
          disabled={signing || !originOk}
          onPress={() => void signInWith(provider)}>
          {LABELS[provider]}
        </Button>
      ))}
      {error ? <HelperText type="error">{error}</HelperText> : null}
    </View>
  );
}
