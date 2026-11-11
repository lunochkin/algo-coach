import { router } from 'expo-router';
import { memo, useMemo, useState } from 'react';
import { SectionList, View } from 'react-native';
import { Appbar, useTheme } from 'react-native-paper';
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
import { fromCopy, Loaded, styles } from '@/ui/common';
import { Heading, PanelItem, PickRow } from '@/ui/rows';

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
      modules.flatMap(({ c, b }) => {
        const groups = lessonGroups(b, c);
        const lessons = groups.reduce((n, g) => n + g.lessons.length, 0);
        return groups.map((g, i) => {
          const key = `${c.slug}:${g.key}`;
          return {
            key,
            c,
            b,
            module: i === 0 ? c.title : null,
            lessons,
            title: g.title,
            total: g.lessons.length,
            data: isOpen(key) ? g.lessons : [],
          };
        });
      }),
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
        <View style={styles.page}>
          <Loaded of="the lessons" state={fromCopy(st, st.catalog ? sections : null)} blank={LESSONS_NONE}>
            {() => null}
          </Loaded>
        </View>
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
              <View style={{ backgroundColor: theme.colors.background, paddingBottom: 4 }}>
                {section.module ? <Heading title={section.module} count={section.lessons} /> : null}
                <Heading
                  sub
                  title={section.title}
                  count={section.total}
                  closed={!expanded}
                  onToggle={() => setOpen((o) => ({ ...o, [section.key]: !expanded }))}
                />
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
