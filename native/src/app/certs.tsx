import { useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  certById,
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
  CERT_LEGEND,
  type CertState,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { Panel } from '@/ui/rows';
import { CertRing, CertSheet } from '@/ui/certs';
import { useStartSheet } from '@/ui/start';
import { fromCopy, Loaded, styles, tones, ScreenHeader } from '@/ui/common';
import { PageSection, type Sections, SectionBar, useSections } from '@/ui/sections';
import { usePullSync } from '@/ui/pull';
import { radius, space, textSize } from '@/ui/tokens';

const CELL = 54;

/** Rows: a course's topics, then the course itself; columns: Foundation to Expert. */
export default function CertsScreen() {
  const st = useStore();
  const pull = usePullSync();
  const starter = useStartSheet();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { open } = useLocalSearchParams<{ open?: string }>();
  const [picked, setPicked] = useState<{ course: string; id: string } | null>(() => {
    const found = certById(st.catalog, open);
    return found && open ? { course: found.c.slug, id: open } : null;
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
      <ScreenHeader title={CERTS_TITLE} />
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
            refreshControl={pull}
            ref={sections.scroll}
            onScroll={sections.onScroll}
            onScrollBeginDrag={sections.onScrollBeginDrag}
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
        <Text variant="labelSmall" style={{ fontSize: textSize.micro, color: theme.colors.onSurfaceVariant }}>
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
        borderRadius: radius(theme).xl,
        backgroundColor: s.state === 'ready' ? theme.colors.primaryContainer : 'transparent',
      }}
    >
      {body}
    </Pressable>
  );
}

// what each shape in the grid stands for: the words are core's, the icons the phone's
function Legend() {
  const theme = useTheme();
  const amber = tones(theme.dark).open;
  const icon: Partial<Record<CertState, [string, string]>> = {
    locked: ['lock-outline', theme.colors.onSurfaceDisabled],
    in_progress: ['circle-slice-3', theme.colors.secondary],
    ready: ['trophy-outline', theme.colors.primary],
    earned: ['trophy', theme.colors.primary],
    needs_refresh: ['refresh', amber],
    insufficient_pool: ['text-box-remove-outline', amber],
  };
  return (
    <View style={[styles.row, { flexWrap: 'wrap', columnGap: 12, rowGap: 4 }]}>
      {CERT_LEGEND.map((one) => {
        const drawn = icon[one.state];
        return (
          <View key={one.state} style={[styles.row, { gap: space[1] }]}>
            {drawn ? (
              <MaterialCommunityIcons name={drawn[0] as never} size={16} color={drawn[1]} />
            ) : (
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {one.sample}
              </Text>
            )}
            <Text variant="labelSmall">{one.label}</Text>
          </View>
        );
      })}
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
      <Panel padded>
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
      </Panel>
    </PageSection>
  );
}
