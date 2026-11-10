import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { Appbar, Button, Card, Chip, IconButton, Snackbar, Text, TouchableRipple, useTheme } from 'react-native-paper';
import ReorderableList, {
  reorderItems,
  useReorderableDrag,
  type ReorderableListReorderEvent,
} from 'react-native-reorderable-list';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  bySavedOrder,
  certStates,
  continueCounts,
  continueLine,
  continuePlan,
  type Course,
  drillQueue,
  emptyContinue,
  focusLabel,
  type Group,
  moduleRows,
  NEW_STEP,
  type NextUpView,
  readyLesson,
  reviewQueue,
} from '@algo-coach/core';
import { APP_NAME } from '@/lib/name';
import { useStore } from '@/lib/store';
import { BottomBar, startQueue, styles, SyncBanner, SyncLine } from '@/ui/common';
import { FocusCard } from '@/ui/focuscard';
import { AccountMenu } from '@/ui/account';

export default function Home() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [notice, setNotice] = useState('');
  const [noticeAction, setNoticeAction] = useState<{ label: string; run: () => void } | null>(null);
  useEffect(() => {
    // the app opens on Login until it holds a token, and returns there on sign-out
    if (st.ready && !st.hasToken) router.replace('/login');
  }, [st.ready, st.hasToken]);

  const { board } = st;
  const b = useMemo(() => board(null), [board]);
  const info = useMemo(() => (b ? { courses: moduleRows(b, Date.now()) } : null), [b]);

  // opening a module is the pick of one module: `pages.md`, The structure
  const { focus } = st;
  const focused = focus;
  const limit = st.newLimit;
  // The queue Continue would open, and the board its picks use.
  const cont = useMemo(() => continuePlan(board, focus, null, limit), [board, focus, limit]);
  const counts = useMemo(() => (cont ? continueCounts(cont, focused, Date.now()) : null), [cont, focused]);

  // The first certificate whose requirements are met but its exam (shown above Continue).
  const readyCert = useMemo(() => {
    const all = board(null);
    if (!all) return null;
    for (const c of bySavedOrder(all.courses, (x) => x.slug, st.courseOrder)) {
      if (!c.certs) continue;
      for (const [id, s] of certStates(all, c, st.catalog?.certExams ?? [])) {
        if (s.state === 'ready') return { id, title: c.certs.get(id)?.title ?? id };
      }
    }
    return null;
  }, [board, st.courseOrder, st.catalog]);

  // The first lesson due to be read (its pretest used up, or pretest 0), in course order.
  const toRead = useMemo(() => {
    const all = board(null);
    return all ? readyLesson(all, st.courseOrder) : null;
  }, [board, st.courseOrder]);

  const start = () => {
    if (!cont || !counts) return;
    if (counts.empty) {
      const empty = emptyContinue({ blocked: counts.blocked, newLimit: st.newLimit, focus: focused });
      setNotice(empty.notice);
      const run = {
        raise: () => {
          void st.raiseNew();
          cont.queue.raise(NEW_STEP);
          startQueue(st, 'next', cont.queue, cont.course, cont.include);
        },
        certs: () => router.push('/certs'),
        'clear-focus': () => void st.setFocus(null),
      };
      setNoticeAction(empty.action && { label: empty.action.label, run: run[empty.action.kind] });
      return;
    }
    startQueue(st, 'next', cont.queue, cont.course, cont.include);
  };

  /** The reviews waiting outside a strict focus: a plain review queue over all served courses. */
  const reviewOutside = () => {
    const all = board(null);
    if (all) startQueue(st, 'review', reviewQueue(all, ['weak', 'due']), null);
  };

  const drillGroup = (g: Group) => {
    const gb = board(g.course);
    if (!gb) return;
    const queue = drillQueue(gb, g, limit);
    if (!queue.isEmpty(gb, Date.now())) startQueue(st, 'drill', queue, g.course);
  };

  const order = st.courseOrder;
  const rows = useMemo(() => bySavedOrder(info?.courses ?? [], (r) => r.c.slug, order), [info, order]);
  const onReorder = ({ from, to }: ReorderableListReorderEvent) => {
    const slugs = reorderItems(rows, from, to).map((r) => r.c.slug);
    void st.setCourseOrder(slugs);
  };

  const body = !st.catalog ? (
    <Card mode="contained">
      <Card.Content>
        <Text variant="bodyLarge">
          {st.ready ? 'No courses yet. Add a token in Settings, then sync.' : 'Loading…'}
        </Text>
      </Card.Content>
    </Card>
  ) : null;
  const header = (
    <View style={{ gap: 12 }}>
      <SyncBanner sync={st.sync} />
      {/* the lessons and the certifications are steps down from the home: `pages.md`, The structure */}
      <View style={styles.row}>
        <Button compact icon="book-open-variant" onPress={() => router.push('/lessons')}>
          Lessons
        </Button>
        <Button compact icon="trophy-outline" onPress={() => router.push('/certs')}>
          Certifications
        </Button>
      </View>
      {body}
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Content title={APP_NAME} />
        <AccountMenu />
      </Appbar.Header>
      <ReorderableList
        data={rows}
        keyExtractor={(r) => r.c.slug}
        onReorder={onReorder}
        ListHeaderComponent={header}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        ListFooterComponent={
          <Pressable onPress={() => st.requestSync(0)} accessibilityLabel="Sync now" style={{ marginTop: 12 }}>
            <SyncLine sync={st.sync} showError={false} />
          </Pressable>
        }
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 160 }}
        renderItem={({ item }) => (
          <CourseCard
            c={item.c}
            view={item.view}
            total={item.total}
            toReview={item.toReview}
            onFrontier={drillGroup}
          />
        )}
      />
      <BottomBar bottom={insets.bottom}>
        {focused && cont ? (
          <FocusCard
            label={focusLabel(focused, st.catalog)}
            focus={focused}
            b={cont.b}
            queue={cont.queue}
            exams={st.catalog?.certExams ?? []}
            onOpen={() => router.push({ pathname: '/module', params: { course: focused.course } })}
            onClear={() => void st.setFocus(null)}
            onStrict={() => void st.setFocus({ ...focused, strict: !focused.strict })}
            onMoreNew={() => void st.raiseNew()}
          />
        ) : (
          <FocusLine
            label={focusLabel(focus, st.catalog)}
            set={!!focus}
            setAside={false}
            onOpen={() => focus && router.push({ pathname: '/module', params: { course: focus.course } })}
            onClear={() => void st.setFocus(null)}
            strict={!!focus?.strict}
            onStrict={() => focus && void st.setFocus({ ...focus, strict: !focus.strict })}
          />
        )}
        {readyCert ? (
          <TouchableRipple
            onPress={() => router.push({ pathname: '/certs', params: { open: readyCert.id } })}
            accessibilityRole="button"
            accessibilityLabel={`Ready for exam: ${readyCert.title}`}
            borderless
            style={{
              minHeight: 48,
              borderRadius: 12,
              paddingHorizontal: 12,
              justifyContent: 'center',
              backgroundColor: theme.colors.primaryContainer,
            }}>
            <View style={styles.row}>
              <MaterialCommunityIcons name="trophy-outline" size={20} color={theme.colors.onPrimaryContainer} />
              <Text variant="bodyMedium" numberOfLines={1} style={{ flex: 1, color: theme.colors.onPrimaryContainer }}>
                {`Ready for exam: ${readyCert.title}`}
              </Text>
            </View>
          </TouchableRipple>
        ) : null}
        {toRead ? (
          <TouchableRipple
            onPress={() =>
              router.push({ pathname: '/lesson', params: { course: toRead.c.slug, slug: toRead.lesson.slug } })
            }
            accessibilityRole="button"
            accessibilityLabel={toRead.line}
            borderless
            style={{
              minHeight: 48,
              borderRadius: 12,
              paddingHorizontal: 12,
              justifyContent: 'center',
              backgroundColor: theme.colors.tertiaryContainer,
            }}>
            <View style={styles.row}>
              <MaterialCommunityIcons name="book-open-variant" size={20} color={theme.colors.onTertiaryContainer} />
              <Text variant="bodyMedium" numberOfLines={1} style={{ flex: 1, color: theme.colors.onTertiaryContainer }}>
                {toRead.line}
              </Text>
            </View>
          </TouchableRipple>
        ) : null}
        <Button
          mode="contained"
          icon="play"
          disabled={!st.catalog}
          onPress={start}
          contentStyle={{ paddingVertical: 8 }}>
          Continue
        </Button>
        {counts ? (
          <View style={[styles.row, { justifyContent: 'center', flexWrap: 'wrap', minHeight: 24 }]}>
            <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              {continueLine(counts, !!focused?.strict)}
            </Text>
            {focused?.strict && counts.outside ? (
              <TouchableRipple
                onPress={reviewOutside}
                borderless
                accessibilityRole="link"
                accessibilityLabel={`Review ${counts.outside} waiting outside the focus`}
                style={{ minHeight: 48, justifyContent: 'center', paddingHorizontal: 4, borderRadius: 8 }}>
                <Text variant="labelMedium" style={{ color: theme.colors.primary, textDecorationLine: 'underline' }}>
                  {` · ${counts.outside} waiting outside`}
                </Text>
              </TouchableRipple>
            ) : null}
          </View>
        ) : null}
        <View style={styles.row}>
          <Button
            mode="contained-tonal"
            icon="clipboard-check-outline"
            style={{ flex: 1 }}
            disabled={!st.catalog}
            onPress={() => router.push('/exam')}>
            Exam
          </Button>
        </View>
      </BottomBar>
      <Snackbar
        visible={!!notice}
        onDismiss={() => {
          setNotice('');
          setNoticeAction(null);
        }}
        duration={noticeAction ? 6000 : 2500}
        action={noticeAction ? { label: noticeAction.label, onPress: noticeAction.run } : undefined}
        wrapperStyle={{ bottom: insets.bottom + 200 }}>
        {notice}
      </Snackbar>
    </View>
  );
}

/** What Continue serves; tap opens Practice on it, ✕ clears it. */
function FocusLine(props: {
  label: string;
  set: boolean;
  setAside: boolean;
  onOpen: () => void;
  onClear: () => void;
  strict: boolean;
  onStrict: () => void;
}) {
  const { label, set, setAside, onOpen, onClear, strict, onStrict } = props;
  const theme = useTheme();
  return (
    <View style={[styles.row, { minHeight: 48 }]}>
      <TouchableRipple
        onPress={onOpen}
        borderless
        accessibilityRole="button"
        accessibilityLabel={`Focus: ${label}${setAside ? ', not used with a course filter' : ''}`}
        accessibilityHint="Opens Practice on the focus"
        style={{ flex: 1, minHeight: 48, justifyContent: 'center', borderRadius: 8, paddingHorizontal: 8 }}>
        <View style={styles.row}>
          <MaterialCommunityIcons name="crosshairs-gps" size={18} color={theme.colors.primary} />
          <Text variant="bodyMedium" numberOfLines={2} style={{ flex: 1 }}>
            <Text style={{ color: theme.colors.onSurfaceVariant }}>Focus: </Text>
            {label}
            {setAside ? (
              <Text style={{ color: theme.colors.onSurfaceVariant }}> · not used with a course filter</Text>
            ) : null}
          </Text>
        </View>
      </TouchableRipple>
      {set ? (
        <Chip
          compact
          selected={strict}
          showSelectedCheck
          onPress={onStrict}
          accessibilityLabel={strict ? 'Strict focus on: reviews from the focus only' : 'Strict focus off: reviews from everywhere'}
          style={{ minHeight: 48, justifyContent: 'center' }}>
          Strict
        </Chip>
      ) : null}
      {set ? (
        <IconButton icon="close" size={20} onPress={onClear} accessibilityLabel="Clear focus" style={{ margin: 0, width: 48, height: 48 }} />
      ) : null}
    </View>
  );
}

/** A course row: tap opens its map, long-press or the handle drags it to reorder. */
function CourseCard({
  c,
  view,
  total,
  toReview,
  onFrontier,
}: {
  c: Course;
  view: NextUpView;
  total: number;
  toReview: number;
  onFrontier: (g: Group) => void;
}) {
  const theme = useTheme();
  const drag = useReorderableDrag();
  return (
    <Card
      mode="outlined"
      onPress={() => router.push({ pathname: '/module', params: { course: c.slug } })}
      onLongPress={drag}
      accessibilityLabel={`Open ${c.title}`}
      accessibilityHint="Opens the module. Long-press to reorder.">
      <Card.Title
        title={c.title}
        subtitle={`${total} questions · ${toReview} to review${c.paused ? ' · paused' : ''}`}
        right={() => (
          <View style={{ flexDirection: 'row' }}>
            <IconButton icon="drag" onPressIn={drag} accessibilityLabel={`Reorder ${c.title}`} />
          </View>
        )}
      />
      <Card.Content>
        {view.next ? (
          <TouchableRipple
            onPress={() => {
              const next = view.next;
              if (!next) return;
              if (next.lesson) router.push({ pathname: '/lesson', params: { course: c.slug, slug: next.lesson.slug } });
              else onFrontier(next.group);
            }}
            borderless
            accessibilityRole="button"
            accessibilityLabel={view.accessibilityLabel}
            style={{ minHeight: 48, justifyContent: 'center', borderRadius: 8, marginHorizontal: -8, paddingHorizontal: 8 }}>
            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <Text variant="bodyMedium" style={{ color: theme.colors.primary }}>
                  {view.title}
                </Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {view.detail}
                </Text>
              </View>
              <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
                ▶
              </Text>
            </View>
          </TouchableRipple>
        ) : (
          <Text variant="bodyMedium">{view.title}</Text>
        )}
      </Card.Content>
    </Card>
  );
}
