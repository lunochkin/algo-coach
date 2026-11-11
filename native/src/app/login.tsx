import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { Button, HelperText, Text, TextInput, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  continueWith,
  devLoginAs,
  LOGIN_INTRO,
  NO_DEV_LOGIN,
  NO_SIGN_IN,
  SIGN_IN_LOADING,
  signInUnread,
  PRIVACY_LINK,
  PRIVACY_NOTE,
  ENGINE_ADDRESS,
  ADDRESS_HINT,
  DEV_LOGIN_INTRO,
  validOrigin,
} from '@algo-coach/core';
import { offered, signIn, type Offered, type Provider } from '@/lib/auth';
import { described } from '@/lib/engine';
import { APP_NAME } from '@/lib/name';
import { useStore } from '@/lib/store';
import { Failed } from '@/ui/common';
import { space } from '@/ui/tokens';

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
  const originOk = validOrigin(origin);
  const [offer, setOffer] = useState<Offered | null>(null);
  const [unread, setUnread] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  // the providers the engine names, read as the web's login reads them
  useEffect(() => {
    const at = origin.trim();
    if (!validOrigin(at)) return;
    let live = true;
    setOffer(null);
    setUnread(null);
    // the address may still be typed: read it once typing pauses
    const wait = setTimeout(() => {
      offered(at).then(
        (one) => {
          if (live) setOffer(one);
        },
        (e: unknown) => {
          if (live) setUnread(described(e));
        },
      );
    }, 400);
    return () => {
      live = false;
      clearTimeout(wait);
    };
  }, [origin, attempt]);

  const providers: Provider[] = offer
    ? [...offer.providers, ...(offer.dev_login === null ? [] : ['dev' as const])]
    : [];
  const label = (p: Provider) => (p === 'dev' ? devLoginAs(offer?.dev_login ?? '') : continueWith(p));

  const signInWith = async (provider: Provider) => {
    setSigning(true);
    setError(null);
    try {
      if (origin.trim() !== st.settings.origin) {
        await st.updateSettings({ ...st.settings, origin: origin.trim() });
      }
      const { token, user } = await signIn(origin.trim(), provider, st.settings.device);
      await st.signedIn(token, user);
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
        gap: space[4],
        padding: space[6],
        paddingTop: insets.top + 24,
        paddingBottom: insets.bottom + 24,
        backgroundColor: theme.colors.background,
      }}
    >
      <Text variant="displaySmall">{APP_NAME}</Text>
      <Text variant="bodyLarge">{__DEV__ ? DEV_LOGIN_INTRO : LOGIN_INTRO}</Text>
      {!st.settings.origin ? (
        <>
          <TextInput
            mode="outlined"
            label={ENGINE_ADDRESS}
            value={origin}
            onChangeText={setOrigin}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          {!originOk ? <HelperText type="error">{ADDRESS_HINT}</HelperText> : null}
        </>
      ) : null}
      {!originOk ? null : unread !== null ? (
        <Failed message={signInUnread(unread)} onRetry={() => setAttempt((n) => n + 1)} />
      ) : offer === null ? (
        <Text variant="bodyMedium">{SIGN_IN_LOADING}</Text>
      ) : providers.length === 0 ? (
        <Text variant="bodyMedium">{__DEV__ ? NO_DEV_LOGIN : NO_SIGN_IN}</Text>
      ) : (
        providers.map((provider) => (
          <Button
            key={provider}
            mode="contained"
            icon={ICONS[provider]}
            loading={signing}
            disabled={signing}
            onPress={() => void signInWith(provider)}
          >
            {label(provider)}
          </Button>
        ))
      )}
      {error ? <HelperText type="error">{error}</HelperText> : null}
      {/* the policy the web's login links, held in the app */}
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {PRIVACY_NOTE}{' '}
        <Text
          variant="bodySmall"
          accessibilityRole="link"
          style={{ color: theme.colors.primary, textDecorationLine: 'underline' }}
          onPress={() => router.push('/privacy')}
        >
          {PRIVACY_LINK}
        </Text>
      </Text>
    </View>
  );
}
