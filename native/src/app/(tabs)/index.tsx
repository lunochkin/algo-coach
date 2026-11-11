import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { Appbar, Button, Card, IconButton, Snackbar, Text, TouchableRipple, useTheme } from 'react-native-paper';
import ReorderableList, {
  reorderItems,
  useReorderableDrag,
  type ReorderableListReorderEvent,
} from 'react-native-reorderable-list';

import {
  bySavedOrder,
  CERTIFICATIONS_LINK,
  CONTINUE,
  continueCounts,
  continueLine,
  continuePlan,
  type Course,
  emptyContinue,
  EXAM_LINK,
  focusLabel,
  LESSONS_LINK,
  MODULES_HEADING,
  moduleStats,
  moduleRows,
  MODULES_LOADING,
  NEW_STEP,
  type NextUpView,
  NO_MODULES,
  PAUSED,
  readyCert,
  readyLesson,
  reviewQueue,
  SYNC_NOW,
  waitingOutside,
} from '@algo-coach/core';
import { APP_NAME } from '@/lib/name';
import { useStore } from '@/lib/store';
import { startQueue, styles, SyncBanner, SyncLine } from '@/ui/common';
import { FocusCard } from '@/ui/focuscard';
import { AccountMenu } from '@/ui/account';
import { Heading, PanelItem, PickRow } from '@/ui/rows';

export default function Home() {
  const st = useStore();
  const theme = useTheme();
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
  const certToTake = useMemo(() => {
    const all = board(null);
    return all ? readyCert(all, st.courseOrder, st.catalog?.certExams ?? []) : null;
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

  const order = st.courseOrder;
  const rows = useMemo(() => bySavedOrder(info?.courses ?? [], (r) => r.c.slug, order), [info, order]);
  const onReorder = ({ from, to }: ReorderableListReorderEvent) => {
    const slugs = reorderItems(rows, from, to).map((r) => r.c.slug);
    void st.setCourseOrder(slugs);
  };

  const body = !st.catalog ? (
    <Card mode="contained">
      <Card.Content>
        <Text variant="bodyLarge">{st.ready ? NO_MODULES : MODULES_LOADING}</Text>
      </Card.Content>
    </Card>
  ) : null;
  const header = (
    <View style={{ gap: 12, marginBottom: 12 }}>
      <SyncBanner sync={st.sync} />
      {/* the lessons and the certifications are steps down from the home: `pages.md`, The structure */}
      <View style={styles.row}>
        <Button compact icon="book-open-variant" onPress={() => router.push('/lessons')}>
          {LESSONS_LINK}
        </Button>
        <Button compact icon="trophy-outline" onPress={() => router.push('/certs')}>
          {CERTIFICATIONS_LINK}
        </Button>
      </View>
      {/* one scroll, in the web's order: the next steps and the focus, the acts,
          then the modules. A bar pinned over the list left the modules a sliver */}
      <View style={{ gap: 8 }}>
        {certToTake ? (
          <TouchableRipple
            onPress={() => router.push({ pathname: '/certs', params: { open: certToTake.id } })}
            accessibilityRole="button"
            accessibilityLabel={certToTake.line}
            borderless
            style={{
              minHeight: 48,
              borderRadius: 12,
              paddingHorizontal: 12,
              justifyContent: 'center',
              backgroundColor: theme.colors.primaryContainer,
            }}
          >
            <View style={styles.row}>
              <MaterialCommunityIcons name="trophy-outline" size={20} color={theme.colors.onPrimaryContainer} />
              <Text variant="bodyMedium" numberOfLines={1} style={{ flex: 1, color: theme.colors.onPrimaryContainer }}>
                {certToTake.line}
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
            }}
          >
            <View style={styles.row}>
              <MaterialCommunityIcons name="book-open-variant" size={20} color={theme.colors.onTertiaryContainer} />
              <Text variant="bodyMedium" numberOfLines={1} style={{ flex: 1, color: theme.colors.onTertiaryContainer }}>
                {toRead.line}
              </Text>
            </View>
          </TouchableRipple>
        ) : null}
        {focused && cont ? (
          <FocusCard
            label={focusLabel(focused, st.catalog)}
            focus={focused}
            b={cont.b}
            queue={cont.queue}
            exams={st.catalog?.certExams ?? []}
            onClear={() => void st.setFocus(null)}
            onStrict={() => void st.setFocus({ ...focused, strict: !focused.strict })}
            onMoreNew={() => void st.raiseNew()}
          />
        ) : null}
        <Button
          mode="contained"
          icon="play"
          disabled={!st.catalog}
          onPress={start}
          contentStyle={{ paddingVertical: 8 }}
        >
          {CONTINUE}
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
                accessibilityLabel={waitingOutside(counts.outside)}
                style={{ minHeight: 48, justifyContent: 'center', paddingHorizontal: 4, borderRadius: 8 }}
              >
                <Text variant="labelMedium" style={{ color: theme.colors.primary, textDecorationLine: 'underline' }}>
                  {` · ${waitingOutside(counts.outside)}`}
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
            onPress={() => router.push('/exam')}
          >
            {EXAM_LINK}
          </Button>
        </View>
      </View>
      {body}
      {rows.length ? <Heading title={MODULES_HEADING} count={rows.length} /> : null}
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
        ListFooterComponent={
          <Pressable onPress={() => st.requestSync(0)} accessibilityLabel={SYNC_NOW} style={{ marginTop: 12 }}>
            <SyncLine sync={st.sync} showError={false} />
          </Pressable>
        }
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item, index }) => (
          <PanelItem first={index === 0} last={index === rows.length - 1}>
            <ModuleRow c={item.c} view={item.view} total={item.total} toReview={item.toReview} />
          </PanelItem>
        )}
      />
      <Snackbar
        visible={!!notice}
        onDismiss={() => {
          setNotice('');
          setNoticeAction(null);
        }}
        duration={noticeAction ? 6000 : 2500}
        action={noticeAction ? { label: noticeAction.label, onPress: noticeAction.run } : undefined}
        wrapperStyle={{ bottom: 16 }}
      >
        {notice}
      </Snackbar>
    </View>
  );
}

/** A module's row: a press opens the module, a long press or the handle drags it to reorder. */
function ModuleRow({ c, view, total, toReview }: { c: Course; view: NextUpView; total: number; toReview: number }) {
  const drag = useReorderableDrag();
  return (
    <PickRow
      title={c.title}
      badge={c.paused ? PAUSED : null}
      stats={moduleStats(toReview, total)}
      note={[view.title, view.detail].filter(Boolean).join(' · ')}
      onPress={() => router.push({ pathname: '/module', params: { course: c.slug } })}
      onLongPress={drag}
      aside={<IconButton icon="drag" onPressIn={drag} accessibilityLabel={`Reorder ${c.title}`} />}
    />
  );
}
