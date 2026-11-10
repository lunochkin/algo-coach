import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { KeyboardAwareScrollView } from 'react-native-keyboard-controller';
import { Appbar, Button, Dialog, HelperText, Portal, Text, TextInput, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useStore } from '@/lib/store';
import { styles, SyncLine } from '@/ui/common';

export default function SettingsScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [signing, setSigning] = useState(false);
  const [unsent, setUnsent] = useState(0);
  const [form, setForm] = useState({
    origin: st.settings.origin,
    device: st.settings.device,
    newPerDay: String(st.newPerDay),
    examSize: String(st.settings.examSize),
    reminderHour: String(st.settings.reminderHour),
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setForm({
      origin: st.settings.origin,
      device: st.settings.device,
      newPerDay: String(st.newPerDay),
      examSize: String(st.settings.examSize),
      reminderHour: String(st.settings.reminderHour),
    });
  }, [st.settings, st.newPerDay]);

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
      examSize,
      reminderHour: hour,
    });
    if (newPerDay !== st.newPerDay) await st.setNewPerDay(newPerDay);
    setSaved(true);
    st.requestSync(0);
  };

  // the outbox goes first. Records it could not send are named before sign-out deletes them
  const signOutHere = async (force: boolean) => {
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
        <View style={styles.row}>
          <Text variant="bodyMedium" style={{ flex: 1 }}>
            {st.hasToken ? 'Signed in on this device.' : 'Not signed in.'}
          </Text>
          {st.hasToken ? (
            <Button mode="outlined" icon="logout" disabled={signing} onPress={() => void signOutHere(false)}>
              Sign out
            </Button>
          ) : null}
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
      <Portal>
        <Dialog visible={unsent > 0} onDismiss={() => setUnsent(0)}>
          <Dialog.Title>Sign out and lose unsent answers?</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium">
              {`${unsent} ${unsent === 1 ? 'record has' : 'records have'} not reached the engine, and signing out deletes this device's copy. Stay signed in and sync later to keep them.`}
            </Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setUnsent(0)}>Stay signed in</Button>
            <Button onPress={() => void signOutHere(true)}>Sign out</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </View>
  );
}
