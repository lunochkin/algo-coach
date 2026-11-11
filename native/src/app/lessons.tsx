import { router } from 'expo-router';
import { memo, useMemo, useRef, useState } from 'react';
import { SectionList, View } from 'react-native';
import { Appbar, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Board,
  type Course,
  type Lesson,
  lessonSections,
  lessonRow,
  LESSONS_NONE,
  LESSONS_TITLE,
  lessonStats,
  modulesInOrder,
  OF,
  sectionOpened,
  sectionToggled,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { fromCopy, Loaded, styles } from '@/ui/common';
import { Heading, PanelItem, PickRow } from '@/ui/rows';
import { SectionBar } from '@/ui/sections';

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
  const [closed, setClosed] = useState<string[]>([]);
  const isOpen = (key: string) => !closed.includes(key);
  const sections = useMemo(
    () =>
      lessonSections(modules).map((x) => ({
        ...x,
        key: x.id,
        total: x.lessons.length,
        data: closed.includes(x.id) ? [] : x.lessons,
      })),
    [modules, closed],
  );

  // the groups as a long screen's sections: a bar jumps to one and marks the
  // one in view, as on every long screen. A virtualised list scrolls by index,
  // and its headers do not stick, since a stuck header covers the one jumped to
  const list = useRef<SectionList<Lesson, (typeof sections)[number]>>(null);
  const [current, setCurrent] = useState<string | null>(null);
  const bar = {
    items: sections.map((x) => ({ id: x.key, label: x.label })),
    current,
    jump: (key: string) => {
      setClosed((was) => sectionOpened(was, key));
      const sectionIndex = sections.findIndex((x) => x.key === key);
      requestAnimationFrame(() => list.current?.scrollToLocation({ sectionIndex, itemIndex: 0, viewOffset: 0 }));
    },
  };
  const onViewable = useRef(({ viewableItems }: { viewableItems: { section?: { key: string } }[] }) => {
    const first = viewableItems.find((one) => one.section);
    if (first?.section) setCurrent(first.section.key);
  }).current;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={LESSONS_TITLE} />
      </Appbar.Header>
      {!sections.length ? (
        <View style={styles.page}>
          <Loaded of={OF.lessons} state={fromCopy(st, st.catalog ? sections : null)} blank={LESSONS_NONE}>
            {() => null}
          </Loaded>
        </View>
      ) : (
        <>
          <SectionBar sections={bar} />
          <SectionList
            ref={list}
            onViewableItemsChanged={onViewable}
            onScrollToIndexFailed={() => {}}
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
                  {section.module ? <Heading title={section.module} count={section.inModule} /> : null}
                  <Heading
                    sub
                    title={section.title}
                    count={section.total}
                    closed={!expanded}
                    onToggle={() => setClosed((was) => sectionToggled(was, section.key))}
                  />
                </View>
              );
            }}
            stickySectionHeadersEnabled={false}
            initialNumToRender={8}
            windowSize={5}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 24 }}
          />
        </>
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
