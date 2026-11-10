import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Chip, IconButton, Menu, Snackbar, Text, TouchableRipple, useTheme } from 'react-native-paper';
import ReorderableList, {
  reorderItems,
  useReorderableDrag,
  type ReorderableListReorderEvent,
} from 'react-native-reorderable-list';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  certStates,
  drillQueue,
  minutesOf,
  focusLabel,
  focusQueue,
  nextQueue,
  outsideFocus,
  reviewQueue,
  type Course,
  type Group,
} from '@/core';
import { bySavedOrder } from '@/lib/order';
import { APP_NAME } from '@/lib/name';
import { useStore } from '@/lib/store';
import { BottomBar, startQueue, styles, SyncBanner, SyncLine } from '@/ui/common';
import { FocusCard } from '@/ui/focuscard';
import { useArchive, usePauseToggle } from '@/ui/pause';

export default function Home() {
  const st = useStore();
  const pause = usePauseToggle();
  const archive = useArchive();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [notice, setNotice] = useState('');
  const [noticeAction, setNoticeAction] = useState<{ label: string; run: () => void } | null>(null);
  useEffect(() => {
    // the app opens on Login until it holds a token, and returns there on sign-out
    if (st.ready && !st.hasToken) router.replace('/login');
  }, [st.ready, st.hasToken]);

  const { board, filter } = st;
  const b = useMemo(() => board(filter), [board, filter]);
  const info = useMemo(() => {
    if (!b) return null;
    const now = Date.now();
    const all = b.questions();
    const courses = b.courses.map((c) => {
      const qs = all.filter((q) => q.course === c.slug);
      // Same count as `learn courses`: ready weak plus due, anywhere in the course.
      const toReview = qs.filter((q) => b.toReview(q, now)).length;
      return { c, front: b.frontier(c)[0], total: qs.length, toReview };
    });
    return { courses };
  }, [b]);

  // A course chip is an explicit selection, like `learn next --course`, so it sets the focus aside.
  const { focus } = st;
  const focused = !filter && focus ? focus : null;
  const limit = st.newLimit;
  // The queue Continue would open, and the board its picks use.
  const cont = useMemo(() => {
    if (focused) {
      const fb = board(null, focused.course);
      return fb ? { b: fb, queue: focusQueue(fb, focused, limit), course: null, include: focused.course } : null;
    }
    return b ? { b, queue: nextQueue(b, limit), course: filter, include: null } : null;
  }, [b, board, focused, filter, limit]);
  const counts = useMemo(() => {
    if (!cont) return null;
    const now = Date.now();
    return {
      reviews: cont.queue.reviews(cont.b, now).length,
      newLeft: cont.queue.newLeft(cont.b, now),
      outside: focused?.strict ? outsideFocus(cont.b, focused, now) : 0,
      empty: cont.queue.isEmpty(cont.b, now),
    };
  }, [cont, focused]);

  // The first certificate whose requirements are met but its exam (shown above Continue).
  const readyCert = useMemo(() => {
    const all = board(null);
    if (!all) return null;
    for (const c of bySavedOrder(all.courses, (x) => x.slug, st.settings.courseOrder)) {
      if (!c.certs) continue;
      for (const [id, s] of certStates(all, c, st.catalog?.certExams ?? [])) {
        if (s.state === 'ready') return { id, title: c.certs.get(id)?.title ?? id };
      }
    }
    return null;
  }, [board, st.settings.courseOrder, st.catalog]);

  // The first lesson due to be read (its pretest used up, or pretest 0), in course order.
  const readyLesson = useMemo(() => {
    const all = board(null);
    if (!all) return null;
    for (const c of bySavedOrder(all.courses, (x) => x.slug, st.settings.courseOrder)) {
      for (const x of all.lessons(c)) {
        if (all.lessonReady(c, x)) {
          const body = c.lessonBodies[x.slug];
          return { c, x, minutes: body ? minutesOf(x, body) : 0 };
        }
      }
    }
    return null;
  }, [board, st.settings.courseOrder]);

  const start = () => {
    if (!cont || !counts) return;
    if (counts.empty) {
      if (focused && focus?.cert) {
        // A targeted certificate with nothing left to learn: its next step is retention or the exam.
        setNotice('Nothing weak, due or new for the targeted certificate. See its requirements and exam.');
        setNoticeAction({ label: 'Certificates', run: () => router.push('/certs') });
      } else if (focused) {
        setNotice('Nothing weak, due or new in the focus.');
        setNoticeAction({ label: 'Clear focus', run: () => void st.setFocus(null) });
      } else setNotice('Nothing due and nothing new unlocked. Try Practice or see Stats.');
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

  const levels = st.catalog?.rules.levels ?? {};
  const order = st.settings.courseOrder;
  const rows = useMemo(() => bySavedOrder(info?.courses ?? [], (r) => r.c.slug, order), [info, order]);
  const chips = useMemo(
    () => bySavedOrder(st.catalog?.courses ?? [], (c) => c.slug, order),
    [st.catalog, order],
  );

  const onReorder = ({ from, to }: ReorderableListReorderEvent) => {
    const slugs = reorderItems(rows, from, to).map((r) => r.c.slug);
    void st.updateSettings({ ...st.settings, courseOrder: slugs });
  };

  const body = !st.catalog ? (
    <Card mode="contained">
      <Card.Content>
        <Text variant="bodyLarge">
          {st.ready ? 'No courses yet. Add a token in Settings, then sync.' : 'Loading…'}
        </Text>
      </Card.Content>
    </Card>
  ) : (
    <View style={{ gap: 12, marginBottom: 12 }}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.row}>
          <Chip selected={!st.filter} showSelectedCheck onPress={() => st.setFilter(null)}>
            All
          </Chip>
          {chips.map((c) => (
            <Chip
              key={c.slug}
              selected={st.filter === c.slug}
              showSelectedCheck
              onPress={() => st.setFilter(st.filter === c.slug ? null : c.slug)}>
              {c.paused ? `${c.title} (paused)` : c.title}
            </Chip>
          ))}
        </View>
      </ScrollView>
    </View>
  );
  const header = (
    <View style={{ gap: 12 }}>
      <SyncBanner sync={st.sync} />
      {body}
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Content title={APP_NAME} />
        <Appbar.Action icon="trophy-outline" onPress={() => router.push('/certs')} accessibilityLabel="Certifications" />
        <Appbar.Action icon="book-open-variant" onPress={() => router.push('/lessons')} accessibilityLabel="Lessons" />
        <Appbar.Action icon="graph-outline" onPress={() => router.push('/map')} accessibilityLabel="Map" />
        <Appbar.Action icon="chart-box-outline" onPress={() => router.push('/stats')} accessibilityLabel="Stats" />
        <Appbar.Action icon="cog-outline" onPress={() => router.push('/settings')} />
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
            front={item.front}
            total={item.total}
            toReview={item.toReview}
            levels={levels}
            onFrontier={drillGroup}
            onTogglePause={pause.ask}
            onArchive={archive.ask}
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
            onOpen={() => router.push('/practice')}
            onClear={() => void st.setFocus(null)}
            onStrict={() => void st.setFocus({ ...focused, strict: !focused.strict })}
            onMoreNew={() => void st.raiseNew()}
          />
        ) : (
          <FocusLine
            label={focusLabel(focus, st.catalog)}
            set={!!focus}
            setAside={!!filter && !!focus}
            onOpen={() => router.push('/practice')}
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
        {readyLesson ? (
          <TouchableRipple
            onPress={() =>
              router.push({ pathname: '/lesson', params: { course: readyLesson.c.slug, slug: readyLesson.x.slug } })
            }
            accessibilityRole="button"
            accessibilityLabel={`Ready to read: ${readyLesson.x.title}`}
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
                {`Ready to read: ${readyLesson.x.title}${readyLesson.minutes ? ` · ~${readyLesson.minutes} min` : ''}`}
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
              {focused?.strict
                ? `Strict focus · ${counts.reviews} reviews · ${counts.newLeft} new left`
                : `${counts.reviews} reviews · ${counts.newLeft} new left today`}
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
            icon="target"
            style={{ flex: 1 }}
            disabled={!st.catalog}
            onPress={() => router.push({ pathname: '/practice', params: st.filter ? { course: st.filter } : {} })}>
            Practice
          </Button>
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
      {pause.dialog}
      {archive.dialog}
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

/** A course row: tap opens Practice, long-press or the handle drags it to reorder. */
function CourseCard({
  c,
  front,
  total,
  toReview,
  levels,
  onFrontier,
  onTogglePause,
  onArchive,
}: {
  c: Course;
  front: Group | undefined;
  total: number;
  toReview: number;
  levels: Record<string, string>;
  onFrontier: (g: Group) => void;
  onTogglePause: (c: Course) => void;
  onArchive: (c: Course) => void;
}) {
  const theme = useTheme();
  const drag = useReorderableDrag();
  const [menu, setMenu] = useState(false);
  return (
    <Card
      mode="outlined"
      onPress={() => router.push({ pathname: '/practice', params: { course: c.slug } })}
      onLongPress={drag}
      accessibilityLabel={`Practice ${c.title}`}
      accessibilityHint="Opens Practice for this course. Long-press to reorder.">
      <Card.Title
        title={c.title}
        subtitle={`${total} questions · ${toReview} to review${c.paused ? ' · paused' : ''}`}
        right={() => (
          <View style={{ flexDirection: 'row' }}>
            <Menu
              visible={menu}
              onDismiss={() => setMenu(false)}
              anchor={
                <IconButton
                  icon="dots-vertical"
                  onPress={() => setMenu(true)}
                  accessibilityLabel={`More actions for ${c.title}`}
                />
              }>
              <Menu.Item
                leadingIcon={c.paused ? 'play' : 'pause'}
                title={c.paused ? 'Resume course' : 'Pause course'}
                accessibilityLabel={`${c.paused ? 'Resume' : 'Pause'} ${c.title}`}
                onPress={() => {
                  setMenu(false);
                  onTogglePause(c);
                }}
              />
              <Menu.Item
                leadingIcon="archive-outline"
                title="Archive course"
                accessibilityLabel={`Archive ${c.title}`}
                onPress={() => {
                  setMenu(false);
                  onArchive(c);
                }}
              />
            </Menu>
            <IconButton icon="drag" onPressIn={drag} accessibilityLabel={`Reorder ${c.title}`} />
          </View>
        )}
      />
      <Card.Content>
        {front ? (
          <TouchableRipple
            onPress={() => onFrontier(front)}
            borderless
            accessibilityRole="button"
            accessibilityLabel={`Practice frontier ${front.topic} ${front.sub} level ${front.level}`}
            style={{ minHeight: 48, justifyContent: 'center', borderRadius: 8, marginHorizontal: -8, paddingHorizontal: 8 }}>
            <View style={styles.row}>
              <Text variant="bodyMedium" style={{ flex: 1, color: theme.colors.primary }}>
                {`Frontier: ${front.topic}/${front.sub} · ${levels[front.level] ?? `L${front.level}`}`}
              </Text>
              <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
                ▶
              </Text>
            </View>
          </TouchableRipple>
        ) : (
          <Text variant="bodyMedium">All unlocked groups done</Text>
        )}
      </Card.Content>
    </Card>
  );
}
