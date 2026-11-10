import { router } from 'expo-router';
import { ScrollView, View } from 'react-native';
import { Button, Dialog, Portal, Text, useTheme, type MD3Theme } from 'react-native-paper';
import Svg, { Circle } from 'react-native-svg';

import {
  type Board,
  certQuestions,
  type CertState,
  type CertStatus,
  type Course,
  levelName,
  shuffle,
  subTitle,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { startExam, styles, tones } from './common';

export const STATE_LABEL: Record<CertState, string> = {
  earned: 'Earned',
  needs_refresh: 'Needs refresh',
  ready: 'Ready for exam',
  in_progress: 'In progress',
  locked: 'Locked',
  empty: 'No questions',
  not_certified: 'Practice only',
  insufficient_pool: 'Not enough questions yet',
};

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
export function CertRing({ status, size = 36, color: override }: { status: CertStatus; size?: number; color?: string }) {
  const theme = useTheme();
  const color = override ?? stateColor(status.state, theme);
  const arc = (r: number, share: number, w: number, key: string) => {
    const len = 2 * Math.PI * r;
    return [
      <Circle key={`${key}b`} cx={size / 2} cy={size / 2} r={r} stroke={theme.colors.outlineVariant} strokeWidth={w} fill="none" />,
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
}) {
  const { c, b, id, states, onClose } = props;
  const status = states.get(id);
  const st = useStore();
  const theme = useTheme();
  const x = c.certs?.get(id);
  if (!x || !status) return null;
  const targeted = st.focus?.cert === id;
  const prereqs = c.certs?.needs(id) ?? [];
  const take = () => {
    const pool = certQuestions(b, c, x).filter((q) => q.format !== 'card');
    const qs = shuffle(pool).slice(0, x.rule.size);
    onClose();
    startExam(st, `cert-${id}`, qs, { course: c.slug, id, passShare: x.rule.passShare });
  };
  const check = (ok: boolean, text: string) => (
    <Text variant="bodyMedium" key={text}>
      <Text style={{ color: ok ? tones(theme.dark).done : theme.colors.error }}>{ok ? '✓ ' : '✗ '}</Text>
      {text}
    </Text>
  );
  const pct = (v: number) => `${Math.round(v * 100)}%`;
  return (
    <Portal>
      <Dialog visible onDismiss={onClose} style={{ maxHeight: '85%' }}>
        <Dialog.Title>{x.title}</Dialog.Title>
        <Dialog.ScrollArea style={{ paddingHorizontal: 24 }}>
          <ScrollView contentContainerStyle={{ gap: 6, paddingVertical: 8 }}>
            <Text variant="labelLarge" style={{ color: stateColor(status.state, theme) }}>
              {STATE_LABEL[status.state]}
            </Text>
            {status.state === 'not_certified' ? (
              <Text variant="bodyMedium">
                {`This level is practice only: no certificate yet. So far ${status.passed}/${status.questions} questions passed. It becomes a certificate once the course enables it (when its question pool is ready).`}
              </Text>
            ) : null}
            {status.state === 'insufficient_pool' ? (
              <Text variant="bodyMedium">
                {`Not enough questions yet for a fair exam: ${status.pool} available, ${Math.ceil(x.rule.minPoolRatio * x.rule.size)} needed (${x.rule.minPoolRatio}× the ${x.rule.size}-question exam). Until then it counts as not earned, so certificates that need it stay locked.`}
              </Text>
            ) : null}
            {prereqs.map((p) => {
              const s = states.get(p)?.state;
              const ok = s === 'earned' || s === 'needs_refresh' || s === 'empty';
              return check(ok, `Prerequisite: ${c.certs?.get(p)?.title ?? p}${ok ? '' : ` (${STATE_LABEL[s ?? 'locked'].toLowerCase()})`}`);
            })}
            {status.state === 'locked' ? (
              <Text variant="labelLarge" style={{ marginTop: 8, color: theme.colors.onSurfaceVariant }}>
                Progress so far (counts once unlocked)
              </Text>
            ) : null}
            {check(status.short.length === 0, `Coverage: ${pct(status.coverage)} of ${status.questions} questions passed`)}
            {check(status.retention >= x.rule.share, `Retention: ${pct(status.retention)} stable ≥ ${x.rule.stabilityDays} days (needs ${pct(x.rule.share)})`)}
            {x.rule.requireExam
              ? check(
                  status.state === 'earned' || status.state === 'needs_refresh',
                  status.lastExam
                    ? `Exam: last ${status.lastExam.score}/${status.lastExam.n} ${status.lastExam.passed ? 'passed' : 'not passed'} (${status.lastExam.t.slice(0, 10)})`
                    : `Exam: ${x.rule.size} questions, pass ${pct(x.rule.passShare)}`,
                )
              : null}
            {status.short.length ? (
              <Text variant="labelLarge" style={{ marginTop: 8 }}>
                To cover
              </Text>
            ) : null}
            {status.short.map((g) => (
              <View key={g.sub} style={styles.row}>
                <Text variant="bodyMedium" style={{ flex: 1 }}>{`${subTitle(c, g.sub)}: ${g.passed}/${g.total}`}</Text>
                <Button
                  compact
                  onPress={() => {
                    onClose();
                    router.push({
                      pathname: '/practice',
                      params: { course: c.slug, topic: g.topic, sub: g.sub, level: String(x.level) },
                    });
                  }}>
                  Practice
                </Button>
              </View>
            ))}
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
              {`${levelName(b.rules, x.level)} · ${x.scope === 'all' ? 'whole course' : x.scope}`}
            </Text>
          </ScrollView>
        </Dialog.ScrollArea>
        <Dialog.Actions>
          <Button onPress={onClose}>Close</Button>
          {status.state !== 'earned' && status.state !== 'empty' ? (
            targeted ? (
              <Button icon="target" onPress={() => void st.setFocus(null)}>
                Untarget
              </Button>
            ) : (
              <Button
                icon="target"
                mode={status.state === 'ready' ? 'text' : 'contained-tonal'}
                onPress={() => {
                  void st.setFocus({
                    course: c.slug,
                    topic: x.scope === 'all' ? null : x.scope,
                    sub: null,
                    strict: !!st.focus?.strict,
                    cert: x.id,
                  });
                  onClose();
                }}>
                Target
              </Button>
            )
          ) : null}
          {status.state === 'ready' ? (
            <Button mode="contained" icon="trophy-outline" onPress={take}>
              Take exam
            </Button>
          ) : null}
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
}
