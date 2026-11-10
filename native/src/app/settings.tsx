import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { KeyboardAwareScrollView } from 'react-native-keyboard-controller';
import { Appbar, Button, HelperText, Text, TextInput, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  ACCOUNT,
  ARCHIVED_MODULES,
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
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
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
          <Text variant="bodyMedium" style={{ flex: 1 }}>
            {st.hasToken ? 'Signed in on this device.' : 'Not signed in.'}
          </Text>
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
          <Button mode="contained" onPress={save} disabled={!valid}>
            {SAVE}
          </Button>
          <Button mode="outlined" icon="sync" onPress={() => st.requestSync(0)}>
            {SYNC_NOW}
          </Button>
          {saved ? <Text variant="bodySmall">{SAVED}</Text> : null}
        </View>
        <SyncLine sync={st.sync} />
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
