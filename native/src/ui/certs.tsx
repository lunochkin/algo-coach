import { router } from 'expo-router';
import { View } from 'react-native';
import { Button, Text, useTheme, type MD3Theme } from 'react-native-paper';
import Svg, { Circle } from 'react-native-svg';

import {
  type Board,
  CERT_START,
  CERT_TAKE_EXAM,
  CERT_TARGET,
  CERT_TO_COVER,
  CERT_UNTARGET,
  certConditions,
  certFocus,
  type CertState,
  type CertStatus,
  type Course,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { Sheet } from '@/ui/sheet';
import type { Scope } from '@/ui/start';
import { styles, tones } from './common';

export function stateColor(state: CertState, theme: MD3Theme): string {
  const tone = tones(theme.dark);
  return {
    earned: tone.done,
    needs_refresh: tone.open,
    ready: theme.colors.primary,
    in_progress: theme.colors.secondary,
    locked: theme.colors.onSurfaceDisabled,
    empty: theme.colors.outlineVariant,
    not_certified: theme.colors.onSurfaceVariant,
    insufficient_pool: tone.open,
  }[state];
}

/** Two arcs: coverage outside, retention inside, in the state's colour. */
export function CertRing({
  status,
  size = 36,
  color: override,
}: {
  status: CertStatus;
  size?: number;
  color?: string;
}) {
  const theme = useTheme();
  const color = override ?? stateColor(status.state, theme);
  const arc = (r: number, share: number, w: number, key: string) => {
    const len = 2 * Math.PI * r;
    return [
      <Circle
        key={`${key}b`}
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke={theme.colors.outlineVariant}
        strokeWidth={w}
        fill="none"
      />,
      <Circle
        key={key}
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke={color}
        strokeWidth={w}
        fill="none"
        strokeDasharray={`${len * Math.max(0, Math.min(1, share))} ${len}`}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />,
    ];
  };
  if (status.state === 'empty') return <View style={{ width: size, height: size }} />;
  const full = status.state === 'earned' || status.state === 'needs_refresh';
  return (
    <Svg width={size} height={size}>
      {full ? <Circle cx={size / 2} cy={size / 2} r={size / 2 - 3} fill={color} /> : null}
      {arc(size / 2 - 3, full ? 1 : status.coverage, 3, 'cov')}
      {arc(size / 2 - 8, full ? 1 : status.retention, 3, 'ret')}
    </Svg>
  );
}

/** Requirements, blockers with links into Practice, the last exam, and "Take exam" when ready. */
export function CertSheet(props: {
  c: Course;
  b: Board;
  id: string;
  states: Map<string, CertStatus>;
  onClose: () => void;
  onPractice: (s: Scope) => void;
}) {
  const { c, b, id, states, onClose, onPractice } = props;
  const status = states.get(id);
  const st = useStore();
  const theme = useTheme();
  const x = c.certs?.get(id);
  const v = certConditions(b, c, id, states, st.focus);
  if (!x || !status || !v) return null;
  // the rule reads first, as on the web: `pages.md`, The knowledge pages
  const take = () => {
    onClose();
    router.push({ pathname: '/exam', params: { cert: id } });
  };
  const check = (ok: boolean, text: string) => (
    <Text variant="bodyMedium" key={text}>
      <Text style={{ color: ok ? tones(theme.dark).done : theme.colors.error }}>{ok ? '✓ ' : '✗ '}</Text>
      {text}
    </Text>
  );
  return (
    <Sheet
      visible
      onDismiss={onClose}
      title={x.title}
      actions={
        <>
          <Button onPress={onClose}>Close</Button>
          {v.offersTarget ? (
            v.targeted ? (
              <Button icon="target" onPress={() => void st.setFocus(null)}>
                {CERT_UNTARGET}
              </Button>
            ) : (
              <Button
                icon="target"
                mode={v.offersExam ? 'text' : 'contained-tonal'}
                onPress={() => {
                  const f = certFocus(c, x.id, !!st.focus?.strict);
                  if (f) void st.setFocus(f);
                  onClose();
                }}
              >
                {CERT_TARGET}
              </Button>
            )
          ) : null}
          {v.offersExam ? (
            <Button mode="contained" icon="trophy-outline" onPress={take}>
              {CERT_TAKE_EXAM}
            </Button>
          ) : null}
        </>
      }
    >
      <View style={{ gap: 6 }}>
        <Text variant="labelLarge" style={{ color: stateColor(status.state, theme) }}>
          {v.label}
        </Text>
        {v.note ? <Text variant="bodyMedium">{v.note}</Text> : null}
        {v.progressNote ? (
          <Text variant="labelLarge" style={{ marginTop: 8, color: theme.colors.onSurfaceVariant }}>
            {v.progressNote}
          </Text>
        ) : null}
        {v.checks.map((x) => check(x.ok, x.text))}
        {v.short.length ? (
          <Text variant="labelLarge" style={{ marginTop: 8 }}>
            {CERT_TO_COVER}
          </Text>
        ) : null}
        {v.short.map((g) => (
          <View key={g.sub} style={styles.row}>
            <Text variant="bodyMedium" style={{ flex: 1 }}>
              {g.line}
            </Text>
            <Button
              compact
              onPress={() => {
                onClose();
                onPractice({ course: c.slug, topic: g.topic, sub: g.sub, level: x.level });
              }}
            >
              {CERT_START}
            </Button>
          </View>
        ))}
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
          {v.scope}
        </Text>
      </View>
    </Sheet>
  );
}
