import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { KeyboardAwareScrollView } from 'react-native-keyboard-controller';
import { Appbar, Button, HelperText, Text, TextInput, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  ACCOUNT,
  ARCHIVED_MODULES,
  named,
  RESTORE,
  SAVE,
  SAVED,
  SETTING_LABEL,
  SETTINGS,
  settingRange,
  SIGN_OUT,
  STUDY,
  SYNC_NOW,
  validSetting,
  waitingToSend,
} from '@algo-coach/core';
import * as DB from '@/lib/db';
import { useStore } from '@/lib/store';
import { meLine, useMe } from '@/ui/account';
import { styles, SyncLine } from '@/ui/common';
import { useSignOut } from '@/ui/signout';

export default function SettingsScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useSignOut();
  const [form, setForm] = useState({
    origin: st.settings.origin,
    device: st.settings.device,
    newPerDay: String(st.newPerDay),
    examSize: String(st.examSize),
    reminderHour: String(st.settings.reminderHour),
  });
  const [saved, setSaved] = useState(false);
  const me = useMe();
  // the outbox, counted again whenever a sync moves it
  const [waiting, setWaiting] = useState(0);
  useEffect(() => {
    let live = true;
    void DB.pending().then((left) => {
      if (live) setWaiting(left.length);
    });
    return () => {
      live = false;
    };
  }, [st.sync]);

  useEffect(() => {
    setForm({
      origin: st.settings.origin,
      device: st.settings.device,
      newPerDay: String(st.newPerDay),
      examSize: String(st.examSize),
      reminderHour: String(st.settings.reminderHour),
    });
  }, [st.settings, st.newPerDay, st.examSize]);

  const newPerDay = Number(form.newPerDay);
  const examSize = Number(form.examSize);
  const hour = Number(form.reminderHour);
  const newOk = validSetting('new_per_day', newPerDay);
  const examOk = validSetting('exam_size', examSize);
  const sizeOk = newOk && examOk;
  const hourOk = Number.isInteger(hour) && hour >= 0 && hour <= 23;
  const deviceOk = /^[A-Za-z0-9_-]+$/.test(form.device);
  const originOk = /^https?:\/\/[^\s/]+$/.test(form.origin.trim());
  const valid = sizeOk && hourOk && deviceOk && originOk;
  const changed =
    form.origin.trim() !== st.settings.origin ||
    form.device !== st.settings.device ||
    hour !== st.settings.reminderHour ||
    newPerDay !== st.newPerDay ||
    examSize !== st.examSize;

  const save = async () => {
    if (!valid) return;
    await st.updateSettings({
      ...st.settings,
      origin: form.origin.trim(),
      device: form.device,
      reminderHour: hour,
    });
    if (newPerDay !== st.newPerDay) await st.setSetting('new_per_day', newPerDay);
    if (examSize !== st.examSize) await st.setSetting('exam_size', examSize);
    setSaved(true);
    st.requestSync(0);
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
        <Appbar.Content title={SETTINGS} />
      </Appbar.Header>
      <KeyboardAwareScrollView
        bottomOffset={24}
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}
        keyboardShouldPersistTaps="handled">
        <Text variant="titleMedium">{ACCOUNT}</Text>
        {field('origin', 'Engine address')}
        {!originOk ? <HelperText type="error">An address such as https://example.invalid</HelperText> : null}
        <View style={styles.row}>
          {st.hasToken ? (
            <View style={{ flex: 1 }}>
              <Text variant="bodyLarge">{named(me)}</Text>
              <Text
                variant="bodySmall"
                style={{ color: theme.colors.onSurfaceVariant, fontFamily: me?.email ? 'monospace' : undefined }}>
                {meLine(me)}
              </Text>
            </View>
          ) : (
            <Text variant="bodyMedium" style={{ flex: 1 }}>
              Not signed in.
            </Text>
          )}
          {st.hasToken ? (
            <Button mode="outlined" icon="logout" disabled={signOut.signing} onPress={signOut.start}>
              {SIGN_OUT}
            </Button>
          ) : null}
        </View>
        {field('device', 'Device name')}
        {!deviceOk ? <HelperText type="error">Letters, digits, - and _ only</HelperText> : null}
        <Text variant="titleMedium">{STUDY}</Text>
        {field('newPerDay', SETTING_LABEL.new_per_day, true)}
        {!newOk ? <HelperText type="error">{settingRange('new_per_day')}</HelperText> : null}
        {field('examSize', SETTING_LABEL.exam_size, true)}
        {!examOk ? <HelperText type="error">{settingRange('exam_size')}</HelperText> : null}
        {field('reminderHour', 'Reminder hour (0–23)', true)}
        {!hourOk ? <HelperText type="error">0–23</HelperText> : null}
        <View style={styles.row}>
          <Button mode="contained" onPress={save} disabled={!valid || !changed}>
            {SAVE}
          </Button>
          <Button mode="outlined" icon="sync" disabled={st.sync.running} onPress={() => st.requestSync(0)}>
            {SYNC_NOW}
          </Button>
          {saved ? <Text variant="bodySmall">{SAVED}</Text> : null}
        </View>
        <SyncLine sync={st.sync} />
        {waiting ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {waitingToSend(waiting)}
          </Text>
        ) : null}
        {st.archived.length ? (
          <>
            <Text variant="titleMedium" style={{ marginTop: 16 }}>
              {ARCHIVED_MODULES}
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
                  {RESTORE}
                </Button>
              </View>
            ))}
          </>
        ) : null}
      </KeyboardAwareScrollView>
      {signOut.dialog}
    </View>
  );
}
