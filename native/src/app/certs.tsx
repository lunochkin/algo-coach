import { router, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Appbar, Card, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  certCell,
  certId,
  certRows,
  CERTS_NONE,
  CERTS_NOTE,
  CERTS_TITLE,
  certStates,
  COURSE_SCOPE,
  levelName,
  levels,
  modulesInOrder,
  practiceShare,
  type CertStatus,
  type Course,
  coverageShare,
  PRACTICE,
  practiceLevel,
  OF,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { CertRing, CertSheet } from '@/ui/certs';
import { useStartSheet } from '@/ui/start';
import { fromCopy, Loaded, styles, tones } from '@/ui/common';
import { PageSection, type Sections, SectionBar, useSections } from '@/ui/sections';

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
  const modules = useMemo(
    () =>
      modulesInOrder(st.catalog?.courses ?? [], st.courseOrder, board, (c) => !!c.certs).map(({ c, b }) => ({
        c,
        b,
        states: certStates(b, c, st.catalog?.certExams ?? []),
      })),
    [st.catalog, st.courseOrder, board],
  );
  const shown = modules.find((m) => m.c.slug === picked?.course);
  const sections = useSections(modules.map(({ c }) => ({ id: c.slug, label: c.title })));

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={CERTS_TITLE} />
      </Appbar.Header>
      {!modules.length ? (
        <View style={styles.page}>
          <Loaded of={OF.certifications} state={fromCopy(st, st.catalog ? modules : null)} blank={CERTS_NONE}>
            {() => null}
          </Loaded>
        </View>
      ) : (
        <>
          <SectionBar sections={sections} />
          <ScrollView
            ref={sections.scroll}
            onScroll={sections.onScroll}
            scrollEventThrottle={32}
            contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}
          >
            <Legend />
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {CERTS_NOTE}
            </Text>
            {modules.map(({ c, states }) => (
              <Matrix
                key={c.slug}
                of={sections}
                c={c}
                states={states}
                onPick={(id) => setPicked({ course: c.slug, id })}
              />
            ))}
          </ScrollView>
        </>
      )}
      {picked && shown ? (
        <CertSheet
          c={shown.c}
          b={shown.b}
          id={picked.id}
          states={shown.states}
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

function Matrix(props: { of: Sections; c: Course; states: Map<string, CertStatus>; onPick: (id: string) => void }) {
  const { c, states, onPick } = props;
  const theme = useTheme();
  const rules = useStore().catalog!.rules;
  const lv = levels(rules);
  const rows = certRows(c);
  return (
    <PageSection of={props.of} id={c.slug} title={c.title} count={rows.length} body="bare">
      <Card mode="outlined">
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
                {r.title}
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
    </PageSection>
  );
}
