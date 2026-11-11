import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { memo, useMemo, useState } from 'react';
import { Pressable, SectionList, View } from 'react-native';
import { Appbar, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Board,
  type Course,
  type Lesson,
  lessonGroups,
  lessonRow,
  LESSONS_NONE,
  LESSONS_TITLE,
  lessonStats,
  modulesInOrder,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { styles } from '@/ui/common';
import { PanelItem, PickRow } from '@/ui/rows';

// every module's lessons, by module, as the web lists them: `pages.md`, The two clients
export default function LessonsScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { board } = st;
  // a module's own board, so a paused module's lessons read too
  const modules = useMemo(
    () => modulesInOrder(st.catalog?.courses ?? [], st.courseOrder, board, (c) => !!c.graph?.lessons.length),
    [st.catalog, st.courseOrder, board],
  );

  // every group is open until the reader closes it: `pages.md`, A page's areas
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const isOpen = (key: string) => open[key] ?? true;
  const sections = useMemo(
    () =>
      modules.flatMap(({ c, b }) =>
        lessonGroups(b, c).map((g, i) => {
          const key = `${c.slug}:${g.key}`;
          return {
            key,
            c,
            b,
            module: i === 0 ? c.title : null,
            title: g.title,
            total: g.lessons.length,
            data: isOpen(key) ? g.lessons : [],
          };
        }),
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [modules, open],
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={LESSONS_TITLE} />
      </Appbar.Header>
      {!sections.length ? (
        <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>{LESSONS_NONE}</Text>
      ) : (
        <SectionList
          sections={sections}
          keyExtractor={(x) => x.slug}
          renderItem={({ item, index, section }) => (
            <PanelItem first={index === 0} last={index === section.data.length - 1}>
              <LessonRow x={item} c={section.c} b={section.b} />
            </PanelItem>
          )}
          renderSectionHeader={({ section }) => {
            const expanded = isOpen(section.key);
            return (
              <View style={{ backgroundColor: theme.colors.background }}>
                {section.module ? (
                  <Text variant="titleMedium" style={{ paddingTop: 12 }}>
                    {section.module}
                  </Text>
                ) : null}
                <Pressable
                  onPress={() => setOpen((o) => ({ ...o, [section.key]: !expanded }))}
                  style={[styles.row, { justifyContent: 'space-between', paddingVertical: 8 }]}
                  accessibilityRole="button"
                  accessibilityState={{ expanded }}
                >
                  <Text variant="titleSmall" style={{ color: theme.colors.primary }}>
                    {`${section.title} · ${section.total}`}
                  </Text>
                  <MaterialCommunityIcons
                    name={expanded ? 'chevron-up' : 'chevron-down'}
                    size={22}
                    color={theme.colors.primary}
                  />
                </Pressable>
              </View>
            );
          }}
          stickySectionHeadersEnabled
          initialNumToRender={8}
          windowSize={5}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 24 }}
        />
      )}
    </View>
  );
}

/** A lesson's row: what it teaches, then its status and its minutes. */
const LessonRow = memo(function LessonRow({ x, c, b }: { x: Lesson; c: Course; b: Board }) {
  const row = lessonRow(b, c, x);
  return (
    <PickRow
      title={x.title}
      stats={lessonStats(row.status, row.minutes)}
      note={row.teaches}
      dim={row.state === 'locked'}
      onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug: x.slug } })}
    />
  );
});
