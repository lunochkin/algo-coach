import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { memo, useMemo, useState } from 'react';
import { Pressable, ScrollView, SectionList, View } from 'react-native';
import { Appbar, Card, Chip, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Board,
  type Course,
  type Lesson,
  levelName,
  minutesOf,
  subTitle,
  bySavedOrder,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { styles } from '@/ui/common';

/** Lessons in graph order: shallowest taught subtopic and lowest level first, then listing order. */
function inGraphOrder(c: Course, lessons: Lesson[]): Lesson[] {
  const key = (x: Lesson) =>
    Math.min(...x.teaches.map(([s, l]) => (c.graph?.depth(s) ?? 0) * 10 + l), Number.MAX_SAFE_INTEGER);
  return lessons.map((x, i) => ({ x, i, k: key(x) })).sort((a, b) => a.k - b.k || a.i - b.i).map((e) => e.x);
}

export default function LessonsScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const courses = useMemo(
    () =>
      bySavedOrder(st.catalog?.courses ?? [], (c) => c.slug, st.courseOrder).filter(
        (c) => c.graph?.lessons.length,
      ),
    [st.catalog, st.courseOrder],
  );
  const [course, setCourse] = useState(
    () => courses.find((c) => c.slug === st.focus?.course)?.slug ?? courses[0]?.slug ?? '',
  );
  const c = courses.find((x) => x.slug === course);
  const { board } = st;
  const b = useMemo(() => board(null), [board]);

  const groups = useMemo(() => {
    if (!c || !b) return null;
    const all = inGraphOrder(c, c.graph?.lessons ?? []);
    return {
      toRead: all.filter((x) => b.lessonState(c, x) === 'available'),
      read: all.filter((x) => b.lessonState(c, x) === 'done'),
      locked: all.filter((x) => b.lessonState(c, x) === 'locked'),
    };
  }, [b, c]);

  const [open, setOpen] = useState<Record<string, boolean>>({ toRead: true, read: true, locked: false });
  const sections = useMemo(() => {
    if (!groups) return [];
    return (
      [
        { key: 'toRead', title: 'To read', items: groups.toRead },
        { key: 'read', title: 'Read', items: groups.read },
        { key: 'locked', title: 'Locked', items: groups.locked },
      ] as const
    )
      .filter((g) => g.items.length)
      .map((g) => ({ key: g.key, title: g.title, total: g.items.length, data: open[g.key] ? g.items : [] }));
  }, [groups, open]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Lessons" />
      </Appbar.Header>
      {courses.length > 1 ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flexGrow: 0 }}>
          <View style={[styles.row, { paddingHorizontal: 16, paddingBottom: 8 }]}>
            {courses.map((x) => (
              <Chip key={x.slug} selected={x.slug === course} showSelectedCheck onPress={() => setCourse(x.slug)}>
                {x.title}
              </Chip>
            ))}
          </View>
        </ScrollView>
      ) : null}
      {!c || !b || !groups ? (
        <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>No lessons yet.</Text>
      ) : (
        <SectionList
          sections={sections}
          keyExtractor={(x) => x.slug}
          renderItem={({ item }) => <LessonCard x={item} c={c} b={b} />}
          renderSectionHeader={({ section }) => (
            <Pressable
              onPress={() => setOpen((o) => ({ ...o, [section.key]: !o[section.key] }))}
              style={[styles.row, { justifyContent: 'space-between', paddingVertical: 8, backgroundColor: theme.colors.background }]}
              accessibilityRole="button"
              accessibilityState={{ expanded: !!open[section.key] }}>
              <Text variant="titleSmall" style={{ color: theme.colors.primary }}>
                {`${section.title} · ${section.total}`}
              </Text>
              <MaterialCommunityIcons
                name={open[section.key] ? 'chevron-up' : 'chevron-down'}
                size={22}
                color={theme.colors.primary}
              />
            </Pressable>
          )}
          ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
          stickySectionHeadersEnabled
          initialNumToRender={8}
          windowSize={5}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 24 }}
        />
      )}
    </View>
  );
}

/** A tinted card: book icon, title, ~minutes, what it teaches, and its pretest or what it needs. */
const LessonCard = memo(function LessonCard({ x, c, b }: { x: Lesson; c: Course; b: Board }) {
  const theme = useTheme();
  const state = b.lessonState(c, x);
  const body = c.lessonBodies[x.slug] ?? '';
  const [sub, level] = x.teaches[0] ?? ['', 0];
  const teaches = `Teaches ${subTitle(c, sub)} · ${levelName(b.rules, level)}${x.teaches.length > 1 ? ` +${x.teaches.length - 1}` : ''}`;
  const status =
    state === 'done'
      ? 'Read'
      : state === 'locked'
        ? `Needs ${b
            .unmetNeeds(c, x)
            .map((r) =>
              r.startsWith('lesson:')
                ? (c.graph?.lesson(r.slice(7))?.title ?? r)
                : `${r.slice(0, r.lastIndexOf('@'))} · ${levelName(b.rules, Number(r.slice(r.lastIndexOf('@') + 1)))}`,
            )
            .join(', ')}`
        : b.lessonReady(c, x)
          ? 'Ready to read'
          : `Pretest ${Math.min(b.tried(c, x), x.pretest)}/${x.pretest}`;
  const tint =
    state === 'locked' ? theme.colors.surfaceVariant : state === 'done' ? theme.colors.secondaryContainer : theme.colors.tertiaryContainer;
  return (
    <Card
      mode="contained"
      style={{ backgroundColor: tint, opacity: state === 'locked' ? 0.7 : 1 }}
      onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug: x.slug } })}
      accessibilityLabel={`${x.title}, ${status}`}>
      <Card.Content style={[styles.row, { gap: 12 }]}>
        <MaterialCommunityIcons
          name={state === 'done' ? 'book-check-outline' : 'book-open-variant'}
          size={28}
          color={theme.colors.onTertiaryContainer}
        />
        <View style={{ flex: 1, gap: 2 }}>
          <Text variant="titleMedium">{x.title}</Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {`${body ? `~${minutesOf(x, body)} min · ` : ''}${teaches}`}
          </Text>
          <Text variant="labelMedium" style={{ color: state === 'available' ? theme.colors.primary : theme.colors.onSurfaceVariant }}>
            {status}
          </Text>
        </View>
      </Card.Content>
    </Card>
  );
});
