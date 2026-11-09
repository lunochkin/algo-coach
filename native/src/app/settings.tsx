import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { KeyboardAwareScrollView } from 'react-native-keyboard-controller';
import { Appbar, Button, HelperText, Text, TextInput, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { signIn, signOut, type Provider } from '@/lib/auth';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { styles, SyncLine } from '@/ui/common';

export default function SettingsScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [signing, setSigning] = useState(false);
  const [signError, setSignError] = useState<string | null>(null);
  const [form, setForm] = useState({
    origin: st.settings.origin,
    device: st.settings.device,
    newPerDay: String(st.settings.newPerDay),
    examSize: String(st.settings.examSize),
    reminderHour: String(st.settings.reminderHour),
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setForm({
      origin: st.settings.origin,
      device: st.settings.device,
      newPerDay: String(st.settings.newPerDay),
    examSize: String(st.settings.examSize),
      reminderHour: String(st.settings.reminderHour),
    });
  }, [st.settings]);

  const newPerDay = Number(form.newPerDay);
  const examSize = Number(form.examSize);
  const hour = Number(form.reminderHour);
  const okSize = (v: number) => Number.isInteger(v) && v >= 1 && v <= 500;
  const newOk = Number.isInteger(newPerDay) && newPerDay >= 0 && newPerDay <= 200;
  const sizeOk = newOk && okSize(examSize);
  const hourOk = Number.isInteger(hour) && hour >= 0 && hour <= 23;
  const deviceOk = /^[A-Za-z0-9_-]+$/.test(form.device);
  const originOk = /^https?:\/\/[^\s/]+$/.test(form.origin.trim());
  const valid = sizeOk && hourOk && deviceOk && originOk;

  const save = async () => {
    if (!valid) return;
    await st.updateSettings({
      ...st.settings,
      origin: form.origin.trim(),
      device: form.device,
      newPerDay,
      examSize,
      reminderHour: hour,
    });
    setSaved(true);
    st.requestSync(0);
  };

  const signInWith = async (provider: Provider) => {
    setSigning(true);
    setSignError(null);
    try {
      await st.updateToken(await signIn(st.settings.origin, provider, st.settings.device));
      st.requestSync(0);
    } catch (e) {
      setSignError(e instanceof Error ? e.message : String(e));
    } finally {
      setSigning(false);
    }
  };

  const signOutHere = async () => {
    setSigning(true);
    try {
      const token = await getToken();
      if (token) await signOut(st.settings.origin, token).catch(() => undefined);
    } finally {
      await st.updateToken('');
      setSigning(false);
    }
  };

  const field = (key: keyof typeof form, label: string, numeric = false) => (
    <TextInput
      mode="outlined"
      label={label}
      value={form[key]}
      onChangeText={(v) => {
        setSaved(false);
        setForm({ ...form, [key]: v });
      }}
      autoCapitalize="none"
      autoCorrect={false}
      keyboardType={numeric ? 'number-pad' : 'default'}
    />
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Settings" />
      </Appbar.Header>
      <KeyboardAwareScrollView
        bottomOffset={24}
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}
        keyboardShouldPersistTaps="handled">
        <Text variant="titleMedium">Account</Text>
        {field('origin', 'Engine address')}
        {!originOk ? <HelperText type="error">An address such as https://example.invalid</HelperText> : null}
        <HelperText type="info">
          {st.hasToken ? 'Signed in on this device.' : 'Not signed in yet: save the address, then sign in.'}
        </HelperText>
        {signError ? <HelperText type="error">{signError}</HelperText> : null}
        <View style={styles.row}>
          {st.hasToken ? (
            <Button mode="outlined" icon="logout" disabled={signing} onPress={() => void signOutHere()}>
              Sign out
            </Button>
          ) : (
            (['google', 'github'] as const).map((provider) => (
              <Button
                key={provider}
                mode="contained-tonal"
                icon={provider}
                disabled={signing || !originOk || form.origin.trim() !== st.settings.origin}
                onPress={() => void signInWith(provider)}>
                {provider === 'google' ? 'Google' : 'GitHub'}
              </Button>
            ))
          )}
        </View>
        {field('device', 'Device name')}
        {!deviceOk ? <HelperText type="error">Letters, digits, - and _ only</HelperText> : null}
        <Text variant="titleMedium">Study</Text>
        {field('newPerDay', 'New questions per day', true)}
        {field('examSize', 'Exam size', true)}
        {!sizeOk ? <HelperText type="error">New per day 0–200, exam size 1–500</HelperText> : null}
        {field('reminderHour', 'Reminder hour (0–23)', true)}
        {!hourOk ? <HelperText type="error">0–23</HelperText> : null}
        <View style={styles.row}>
          <Button mode="contained" onPress={save} disabled={!valid}>
            Save
          </Button>
          <Button mode="outlined" icon="sync" onPress={() => st.requestSync(0)}>
            Sync now
          </Button>
          {saved ? <Text variant="bodySmall">Saved</Text> : null}
        </View>
        <SyncLine sync={st.sync} />
        {st.archived.length ? (
          <>
            <Text variant="titleMedium" style={{ marginTop: 16 }}>
              Archived courses
            </Text>
            {st.archived.map((c) => (
              <View key={c.slug} style={styles.row}>
                <Text variant="bodyLarge" style={{ flex: 1 }}>
                  {c.title}
                </Text>
                <Button
                  mode="outlined"
                  icon="archive-arrow-up-outline"
                  accessibilityLabel={`Restore ${c.title}`}
                  onPress={() => void st.setCourseStatus(c.slug, 'active')}>
                  Restore
                </Button>
              </View>
            ))}
          </>
        ) : null}
      </KeyboardAwareScrollView>
    </View>
  );
}
