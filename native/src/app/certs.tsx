import { router, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Appbar, Card, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  bySavedOrder,
  certCell,
  certId,
  CERTS_NONE,
  CERTS_NOTE,
  CERTS_TITLE,
  certStates,
  COURSE_SCOPE,
  levelName,
  levels,
  practiceShare,
  type CertStatus,
  type Course,
  coverageShare,
  PRACTICE,
  practiceLevel,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { CertRing, CertSheet } from '@/ui/certs';
import { useStartSheet } from '@/ui/start';
import { styles, tones } from '@/ui/common';

const CELL = 54;

/** Rows: a course's topics, then the course itself; columns: Foundation to Expert. */
export default function CertsScreen() {
  const st = useStore();
  const starter = useStartSheet();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { open } = useLocalSearchParams<{ open?: string }>();
  const [picked, setPicked] = useState<{ course: string; id: string } | null>(() => {
    const c = st.catalog?.courses.find((x) => open && x.certs?.get(open));
    return c && open ? { course: c.slug, id: open } : null;
  });
  const { board } = st;
  const b = useMemo(() => board(null), [board]);
  const courses = useMemo(
    () => bySavedOrder(st.catalog?.courses ?? [], (c) => c.slug, st.courseOrder).filter((c) => c.certs),
    [st.catalog, st.courseOrder],
  );
  const states = useMemo(
    () =>
      new Map(
        courses.map((c) => [c.slug, b ? certStates(b, c, st.catalog?.certExams ?? []) : new Map<string, CertStatus>()]),
      ),
    [b, courses, st.catalog],
  );
  const pickedCourse = courses.find((c) => c.slug === picked?.course);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={CERTS_TITLE} />
      </Appbar.Header>
      {!courses.length || !b ? (
        <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>{CERTS_NONE}</Text>
      ) : (
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
          <Legend />
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {CERTS_NOTE}
          </Text>
          {courses.map((c) => (
            <Matrix
              key={c.slug}
              c={c}
              states={states.get(c.slug)!}
              onPick={(id) => setPicked({ course: c.slug, id })}
            />
          ))}
        </ScrollView>
      )}
      {picked && pickedCourse && b ? (
        <CertSheet
          c={pickedCourse}
          b={b}
          id={picked.id}
          states={states.get(pickedCourse.slug)!}
          onClose={() => setPicked(null)}
          onPractice={starter.open}
        />
      ) : null}
      {starter.sheet}
    </View>
  );
}

/** One cell per state, distinct at a glance; every cell is a 48dp-plus target except "—". */
function Cell(props: { status: CertStatus; title: string; onPress: () => void }) {
  const { status: s, title, onPress } = props;
  const theme = useTheme();
  if (s.state === 'not_certified') {
    // Practice only: progress as passed/total, no state.
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={certCell(title, s)}
        style={{ width: CELL, minHeight: 52, alignItems: 'center', justifyContent: 'center', opacity: 0.6 }}
      >
        <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {practiceShare(s)}
        </Text>
      </Pressable>
    );
  }
  if (s.state === 'empty') {
    return (
      <View style={{ width: CELL, minHeight: 48, alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: theme.colors.outlineVariant }}>—</Text>
      </View>
    );
  }
  const amber = tones(theme.dark).open;
  const body =
    s.state === 'insufficient_pool' ? (
      <MaterialCommunityIcons name="text-box-remove-outline" size={22} color={amber} />
    ) : s.state === 'locked' ? (
      <MaterialCommunityIcons name="lock-outline" size={20} color={theme.colors.onSurfaceDisabled} />
    ) : s.state === 'earned' ? (
      <MaterialCommunityIcons name="trophy" size={24} color={theme.colors.primary} />
    ) : s.state === 'ready' ? (
      <MaterialCommunityIcons name="trophy-outline" size={24} color={theme.colors.onPrimaryContainer} />
    ) : s.state === 'needs_refresh' ? (
      <View style={{ alignItems: 'center', justifyContent: 'center' }}>
        <CertRing status={{ ...s, state: 'in_progress', coverage: 1, retention: s.retention }} color={amber} />
        <View style={{ position: 'absolute' }}>
          <MaterialCommunityIcons name="refresh" size={14} color={amber} />
        </View>
      </View>
    ) : (
      <>
        <CertRing status={s} />
        <Text variant="labelSmall" style={{ fontSize: 10, color: theme.colors.onSurfaceVariant }}>
          {coverageShare(s.coverage)}
        </Text>
      </>
    );
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={certCell(title, s)}
      style={{
        width: CELL,
        minHeight: 52,
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 12,
        backgroundColor: s.state === 'ready' ? theme.colors.primaryContainer : 'transparent',
      }}
    >
      {body}
    </Pressable>
  );
}

function Legend() {
  const theme = useTheme();
  const amber = tones(theme.dark).open;
  const item = (icon: string, color: string, label: string) => (
    <View key={label} style={[styles.row, { gap: 4 }]}>
      <MaterialCommunityIcons name={icon as never} size={16} color={color} />
      <Text variant="labelSmall">{label}</Text>
    </View>
  );
  return (
    <View style={[styles.row, { flexWrap: 'wrap', columnGap: 12, rowGap: 4 }]}>
      {item('lock-outline', theme.colors.onSurfaceDisabled, 'locked')}
      {item('circle-slice-3', theme.colors.secondary, 'in progress')}
      {item('trophy-outline', theme.colors.primary, 'ready for exam')}
      {item('trophy', theme.colors.primary, 'earned')}
      {item('refresh', amber, 'needs refresh')}
      {item('text-box-remove-outline', amber, 'not enough questions yet')}
      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
        n/m practice only
      </Text>
      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
        — no questions
      </Text>
    </View>
  );
}

function Matrix(props: { c: Course; states: Map<string, CertStatus>; onPick: (id: string) => void }) {
  const { c, states, onPick } = props;
  const theme = useTheme();
  const rules = useStore().catalog!.rules;
  const lv = levels(rules);
  const rows = [...c.topics.map((t) => ({ scope: t.slug, label: t.title })), { scope: COURSE_SCOPE, label: c.title }];
  return (
    <Card mode="outlined">
      <Card.Title title={c.title} />
      <Card.Content>
        <View style={styles.row}>
          <View style={{ flex: 1 }} />
          {lv.map((l) => {
            const practice = practiceLevel(c, l);
            return (
              <Text
                key={l}
                variant="labelSmall"
                style={{
                  width: CELL,
                  textAlign: 'center',
                  color: theme.colors.onSurfaceVariant,
                  opacity: practice ? 0.6 : 1,
                }}
              >
                {practice ? `${levelName(rules, l, true)}\n${PRACTICE}` : levelName(rules, l, true)}
              </Text>
            );
          })}
        </View>
        {rows.map((r) => (
          <View key={r.scope} style={[styles.row, { minHeight: 52 }]}>
            <Text
              variant={r.scope === COURSE_SCOPE ? 'titleSmall' : 'bodyMedium'}
              style={{ flex: 1 }}
              numberOfLines={1}
              adjustsFontSizeToFit
              minimumFontScale={0.7}
            >
              {r.label}
            </Text>
            {lv.map((l) => {
              const id = certId(c.slug, r.scope, l);
              const s = states.get(id);
              if (!s) return <View key={l} style={{ width: CELL }} />;
              return <Cell key={l} status={s} title={c.certs?.get(id)?.title ?? id} onPress={() => onPick(id)} />;
            })}
          </View>
        ))}
      </Card.Content>
    </Card>
  );
}
