import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { memo, useMemo, useState } from 'react';
import { Pressable, ScrollView, SectionList, View } from 'react-native';
import { Appbar, Card, Chip, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Board,
  bySavedOrder,
  type Course,
  type Lesson,
  lessonGroups,
  lessonRow,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { styles } from '@/ui/common';

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

  const groups = useMemo(() => (c && b ? lessonGroups(b, c) : null), [b, c]);

  const [open, setOpen] = useState<Record<string, boolean>>({ toRead: true, read: true, locked: false });
  const sections = useMemo(
    () => (groups ?? []).map((g) => ({ key: g.key, title: g.title, total: g.lessons.length, data: open[g.key] ? g.lessons : [] })),
    [groups, open],
  );

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
  const { state, minutes, teaches, status } = lessonRow(b, c, x);
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
            {`${minutes ? `~${minutes} min · ` : ''}${teaches}`}
          </Text>
          <Text variant="labelMedium" style={{ color: state === 'available' ? theme.colors.primary : theme.colors.onSurfaceVariant }}>
            {status}
          </Text>
        </View>
      </Card.Content>
    </Card>
  );
});
