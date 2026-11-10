import { router } from 'expo-router';
import { useMemo } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Board,
  type Course,
  groupCell,
  groupLabel,
  levelName,
  levels,
  newToday,
  subsByDepth,
  summary,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { styles, tones } from '@/ui/common';
import { useStartSheet, type Scope } from '@/ui/start';


export default function Stats() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { board, filter, sessions } = st;
  const b = useMemo(() => board(filter), [board, filter]);
  const sum = useMemo(() => (b ? summary(b, Date.now()) : null), [b]);
  const recent = sessions.slice(-8);
  const { done, open } = tones(theme.dark);
  const starter = useStartSheet();

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Stats" />
        <Appbar.Action icon="graph-outline" onPress={() => router.push('/map')} accessibilityLabel="Map" />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        {!b || !sum ? (
          <Text>No courses yet.</Text>
        ) : (
          <>
            <Card mode="contained">
              <Card.Content style={{ gap: 4 }}>
                <Text variant="titleMedium">
                  {`${sum.questions} questions · ${sum.passed} passed · ${sum.mastered} mastered`}
                </Text>
                <Text variant="bodyMedium">
                  {`${sum.due} due · ${sum.weak} weak · ${sum.soon} more due within 7 days`}
                </Text>
                <Text variant="bodyMedium">
                  {`new today: ${newToday(b, Date.now())}/${st.newLimit}`}
                </Text>
                <View style={[styles.row, { marginTop: 4 }]}>
                  <Legend color={done} label="done" />
                  <Legend color={open} label="unlocked" />
                  <Legend color={theme.colors.onSurfaceDisabled} label="locked" />
                </View>
                <View style={styles.row}>
                  <Text variant="bodySmall" style={{ flex: 1, color: theme.colors.onSurfaceVariant }}>
                    Tap a cell to start a queue on it.
                  </Text>
                  <Button compact icon="graph-outline" onPress={() => router.push('/map')}>
                    Map
                  </Button>
                  <Button compact icon="trophy-outline" onPress={() => router.push('/certs')}>
                    Certs
                  </Button>
                </View>
              </Card.Content>
            </Card>
            {b.courses.map((c) => (
              <CourseCard key={c.slug} b={b} c={c} onPractice={starter.open} />
            ))}
            {recent.length ? (
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {'recent: ' +
                  recent.map((s) => `${s.mode} ${Math.round((100 * s.score) / s.n)}%`).join('  ')}
              </Text>
            ) : null}
          </>
        )}
      </ScrollView>
      {starter.sheet}
    </View>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <Text variant="labelSmall" style={{ color }}>
      {`■ ${label}`}
    </Text>
  );
}

function CourseCard({ b, c, onPractice }: { b: Board; c: Course; onPractice: (s: Scope) => void }) {
  const theme = useTheme();
  const lv = levels(b.rules);
  const front = b.frontier(c)[0];
  const { done, open } = tones(theme.dark);
  return (
    <Card mode="outlined">
      <Card.Title title={c.title} subtitle={c.paused ? `${c.slug} · paused` : c.slug} />
      <Card.Content style={{ gap: 12 }}>
        {c.graphErrors.length ? (
          <Text variant="labelSmall" style={{ color: theme.colors.error }}>
            {`Prerequisite graph ignored (everything open by graph): ${c.graphErrors[0]}`}
          </Text>
        ) : null}
        {c.topics.map((t) => (
          <View key={t.slug} style={{ gap: 2 }}>
            <Text variant="titleSmall">{`T${t.tier} ${t.slug}`}</Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {t.title}
            </Text>
            <View style={[styles.row, { marginTop: 4 }]}>
              <View style={{ flex: 1 }} />
              {lv.map((l) => (
                <Text key={l} variant="labelSmall" style={cellStyle}>
                  {levelName(b.rules, l, true)}
                </Text>
              ))}
            </View>
            {subsByDepth(c, t).map((sub) => (
              <View key={sub} style={styles.row}>
                <View style={{ flex: 1 }}>
                  <Text variant="bodyMedium" numberOfLines={1}>
                    {sub}
                  </Text>
                  {(() => {
                    const need = lv.map((level) => b.needsLabel({ course: c.slug, topic: t.slug, sub, level })).find(Boolean);
                    return need ? (
                      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }} numberOfLines={2}>
                        {need}
                      </Text>
                    ) : null;
                  })()}
                </View>
                {lv.map((level) => {
                  const cell = groupCell(b, { course: c.slug, topic: t.slug, sub, level });
                  const color = { covered: done, open, locked: theme.colors.onSurfaceDisabled, empty: theme.colors.onSurfaceDisabled }[cell.state];
                  return (
                    <Pressable
                      key={level}
                      disabled={cell.state === 'empty'}
                      accessibilityLabel={`Start ${sub} ${levelName(b.rules, level)}`}
                      onPress={() => onPractice({ course: c.slug, topic: t.slug, sub, level })}>
                      <Text variant="bodyMedium" style={[cellStyle, { color }]}>
                        {cell.count}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            ))}
          </View>
        ))}
        {front ? (
          <Text variant="bodyMedium">
            {`Next up: ${groupLabel(c, b.rules, front)}`}
          </Text>
        ) : null}
      </Card.Content>
    </Card>
  );
}

const cellStyle = { width: 56, textAlign: 'right' as const, fontVariant: ['tabular-nums' as const] };
