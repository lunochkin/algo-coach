import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import {
  Appbar,
  Button,
  Chip,
  Switch,
  Text,
  useTheme,
} from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { drillQueue, levelName, levels, subsByDepth, unlocksLabel, sameFocus, type Board, type Course, type Focus, type Topic } from '@/core';
import { bySavedOrder, withFirst } from '@/lib/order';
import { useStore } from '@/lib/store';
import { BottomBar, startQueue, styles } from '@/ui/common';
import { usePauseToggle } from '@/ui/pause';

type Params = { course?: string; topic?: string; sub?: string; level?: string };

export default function Practice() {
  const st = useStore();
  const pause = usePauseToggle();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const p = useLocalSearchParams<Params>();
  const saved = useMemo(
    () => bySavedOrder(st.catalog?.courses ?? [], (c) => c.slug, st.settings.courseOrder),
    [st.catalog, st.settings.courseOrder],
  );
  // The course the screen opened on leads; fixed at open so chips don't jump when another is tapped.
  // Opens on an explicit course, else on the focus, else the first course.
  const [opened] = useState(
    () => saved.find((c) => c.slug === (p.course ?? st.focus?.course))?.slug ?? saved[0]?.slug ?? '',
  );
  const courses = useMemo(() => withFirst(saved, (c) => c.slug, opened), [saved, opened]);
  const [course, setCourse] = useState(opened);
  // An explicit target (a Stats cell) wins over the focus.
  const [initial] = useState(() =>
    p.topic
      ? { topic: p.topic, sub: p.sub ?? null }
      : !p.course && st.focus?.course === opened
        ? { topic: st.focus.topic, sub: st.focus.sub }
        : { topic: null, sub: null },
  );
  // Only the learner's own taps move the focus, not opening the screen.
  const [touched, setTouched] = useState(false);
  const [topic, setTopic] = useState<string | null>(initial.topic);
  const [sub, setSub] = useState<string | null>(initial.sub);
  const [level, setLevel] = useState<number | null>(p.level ? Number(p.level) : null);
  const [kind, setKind] = useState<string | null>(null);
  const [due, setDue] = useState(false);
  const [open, setOpen] = useState<Set<string>>(new Set(initial.topic ? [initial.topic] : []));

  const { board } = st;
  const b = useMemo(() => board(null), [board]);
  const c = courses.find((x) => x.slug === course);
  const limit = st.settings.newPerDay;
  // What Start would open: counts of ready reviews and new left today in this scope.
  const preview = useMemo(() => {
    if (!b || !course) return null;
    const now = Date.now();
    const queue = drillQueue(b, { course, topic, sub, level, kind, due }, limit);
    return {
      queue,
      reviews: queue.reviews(b, now).length,
      newLeft: queue.newLeft(b, now),
      empty: queue.isEmpty(b, now),
    };
  }, [b, course, topic, sub, level, kind, due, limit]);

  const pickCourse = (slug: string) => {
    setTouched(true);
    setCourse(slug);
    setTopic(null);
    setSub(null);
    setKind(null);
    setOpen(new Set());
  };

  // The selection becomes the shared focus after a pause, and on leaving if still pending.
  const { focus, setFocus } = st;
  const pending = useRef<Focus | null>(null);
  useEffect(() => {
    const next: Focus = { course, topic, sub, strict: !!focus?.strict };
    if (!touched || !course || sameFocus(next, focus)) {
      pending.current = null;
      return;
    }
    pending.current = next;
    const timer = setTimeout(() => {
      pending.current = null;
      void setFocus(next);
    }, 1500);
    return () => clearTimeout(timer);
  }, [touched, course, topic, sub, focus, setFocus]);
  useEffect(
    () => () => {
      if (pending.current) void setFocus(pending.current);
    },
    [setFocus],
  );

  const pickTopic = (t: string) => {
    setTouched(true);
    const next = new Set(open);
    if (topic === t && !sub) {
      setTopic(null);
      next.delete(t);
    } else {
      setTopic(t);
      setSub(null);
      next.add(t);
    }
    setOpen(next);
  };
  const pickSub = (t: string, s: string, lvl?: number) => {
    setTouched(true);
    if (lvl === undefined && topic === t && sub === s) return setSub(null);
    setTopic(t);
    setSub(s);
    if (lvl !== undefined) setLevel(lvl);
  };

  const start = () => {
    if (!preview || preview.empty) return;
    startQueue(st, 'drill', preview.queue, course);
  };

  const tiers = c ? [...new Set(c.topics.map((t) => t.tier))] : [];

  return (
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Practice" />
      </Appbar.Header>
      <ScrollView
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 96 }]}
        keyboardShouldPersistTaps="handled">
        {courses.length > 1 ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.row}>
              {courses.map((x) => (
                <Chip
                  key={x.slug}
                  selected={x.slug === course}
                  showSelectedCheck
                  onPress={() => pickCourse(x.slug)}>
                  {x.paused ? `${x.title} (paused)` : x.title}
                </Chip>
              ))}
            </View>
          </ScrollView>
        ) : null}
        <View style={styles.row}>
          <Text variant="bodyMedium" style={{ flex: 1, color: theme.colors.onSurfaceVariant }}>
            {topic ? `Selected: ${topic}${sub ? `/${sub}` : ''}` : `Selected: all of ${c?.title ?? ''}`}
          </Text>
          {c ? (
            <Button
              mode="text"
              compact
              icon={c.paused ? 'play' : 'pause'}
              contentStyle={{ minHeight: 48 }}
              accessibilityLabel={`${c.paused ? 'Resume' : 'Pause'} ${c.title}`}
              onPress={() => pause.ask(c)}>
              {c.paused ? 'Resume course' : 'Pause course'}
            </Button>
          ) : null}
        </View>
        {b && c
          ? tiers.map((tier) => (
              <View key={tier} style={{ gap: 4 }}>
                <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
                  {`Tier ${tier}`}
                </Text>
                {c.topics
                  .filter((t) => t.tier === tier)
                  .map((t) => (
                    <TopicRow
                      key={t.slug}
                      b={b}
                      c={c}
                      t={t}
                      open={open.has(t.slug)}
                      selected={topic === t.slug && !sub}
                      selectedSub={topic === t.slug ? sub : null}
                      onTopic={() => pickTopic(t.slug)}
                      onSub={(s, lvl) => pickSub(t.slug, s, lvl)}
                    />
                  ))}
              </View>
            ))
          : null}

        <Text variant="titleSmall">Level</Text>
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Chip selected={level === null} onPress={() => setLevel(null)}>
            All
          </Chip>
          {(st.catalog ? levels(st.catalog.rules) : []).map((l) => (
            <Chip key={l} selected={level === l} onPress={() => setLevel(level === l ? null : l)}>
              {st.catalog ? levelName(st.catalog.rules, l) : `L${l}`}
            </Chip>
          ))}
        </View>
        {c && c.kinds.length > 1 ? (
          <>
            <Text variant="titleSmall">Kind</Text>
            <View style={[styles.row, { flexWrap: 'wrap' }]}>
              <Chip selected={kind === null} onPress={() => setKind(null)}>
                All
              </Chip>
              {c.kinds.map((k) => (
                <Chip key={k} selected={kind === k} onPress={() => setKind(kind === k ? null : k)}>
                  {k}
                </Chip>
              ))}
            </View>
          </>
        ) : null}
        <View style={styles.row}>
          <Switch value={due} onValueChange={setDue} />
          <Text variant="bodyMedium" onPress={() => setDue(!due)}>
            Only reviews
          </Text>
        </View>
      </ScrollView>
      <BottomBar bottom={insets.bottom}>
        <Button
          mode="contained"
          icon="play"
          disabled={!preview || preview.empty}
          onPress={start}
          contentStyle={{ paddingVertical: 8 }}>
          {!preview || preview.empty
            ? 'Nothing ready here'
            : `Start · ${preview.reviews} reviews · ${preview.newLeft} new left today`}
        </Button>
      </BottomBar>
      {pause.dialog}
    </KeyboardAvoidingView>
  );
}

function TopicRow(props: {
  b: Board;
  c: Course;
  t: Topic;
  open: boolean;
  selected: boolean;
  selectedSub: string | null;
  onTopic: () => void;
  onSub: (sub: string, level?: number) => void;
}) {
  const { b, c, t, open, selected, selectedSub, onTopic, onSub } = props;
  const theme = useTheme();
  const lv = levels(b.rules);
  const now = Date.now();
  // "Foundation 0/56 · Associate 12/56 · Professional —": passed/total per level; — means none written.
  const summary = lv
    .map((level) => {
      const gs = t.subs.map((sub) => ({ course: c.slug, topic: t.slug, sub, level }));
      const total = gs.reduce((n, g) => n + b.groupQuestions(g).length, 0);
      const done = gs.reduce((n, g) => n + b.nPassed(g), 0);
      return `${levelName(b.rules, level)} ${total ? `${done}/${total}` : '—'}`;
    })
    .join(' · ');
  const hi = (on: boolean) => (on ? theme.colors.secondaryContainer : 'transparent');
  return (
    <View style={{ borderRadius: 12, borderWidth: 1, borderColor: theme.colors.outlineVariant }}>
      <Pressable
        onPress={onTopic}
        style={[styles.row, { padding: 12, borderRadius: 12, backgroundColor: hi(selected) }]}>
        <MaterialCommunityIcons
          name={open ? 'chevron-down' : 'chevron-right'}
          size={20}
          color={theme.colors.onSurfaceVariant}
        />
        <View style={{ flex: 1 }}>
          <Text variant="titleSmall">{t.title}</Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {open ? t.slug : summary}
          </Text>
        </View>
      </Pressable>
      {open ? (
        <View style={[styles.row, { paddingHorizontal: 12 }]}>
          <View style={{ flex: 1 }} />
          <View style={{ width: 28 }} />
          {lv.map((level) => (
            <Text key={level} variant="labelSmall" style={{ width: 52, textAlign: 'right', color: theme.colors.onSurfaceVariant }}>
              {levelName(b.rules, level, true)}
            </Text>
          ))}
        </View>
      ) : null}
      {open
        ? subsByDepth(c, t).map((s) => {
            const review = lv
              .flatMap((level) => b.groupQuestions({ course: c.slug, topic: t.slug, sub: s, level }))
              .filter((q) => b.toReview(q, now)).length;
            return (
              <Pressable
                key={s}
                onPress={() => onSub(s)}
                style={[
                  styles.row,
                  { paddingVertical: 8, paddingHorizontal: 12, backgroundColor: hi(selectedSub === s) },
                ]}>
                <View style={{ flex: 1 }}>
                  <Text variant="bodyMedium" numberOfLines={1}>
                    {s}
                  </Text>
                  {[
                    lv.map((level) => b.needsLabel({ course: c.slug, topic: t.slug, sub: s, level })).find(Boolean),
                    unlocksLabel(c, s),
                  ]
                    .filter(Boolean)
                    .map((line) => (
                      <Text key={line} variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }} numberOfLines={2}>
                        {line}
                      </Text>
                    ))}
                  {(() => {
                    // One small book chip per subtopic: the first lesson still to read, else the first.
                    const ls = (c.graph?.lessons ?? []).filter((x) => x.teaches.some(([ts]) => ts === s));
                    const x = ls.find((y) => !b.lessonDone(c, y)) ?? ls[0];
                    return x ? (
                      <Chip
                        compact
                        icon="book-open-variant"
                        style={{ alignSelf: 'flex-start', marginTop: 4 }}
                        accessibilityLabel={`Lesson: ${x.title}`}
                        onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug: x.slug } })}>
                        {ls.length > 1 ? `${ls.length} lessons` : b.lessonDone(c, x) ? 'lesson ✓' : 'lesson'}
                      </Chip>
                    ) : null;
                  })()}
                </View>
                <Text
                  variant="labelSmall"
                  style={{ width: 28, textAlign: 'right', color: review ? theme.colors.error : theme.colors.onSurfaceDisabled }}>
                  {review ? `${review}↻` : ''}
                </Text>
                {lv.map((level) => {
                  const g = { course: c.slug, topic: t.slug, sub: s, level };
                  const n = b.groupQuestions(g).length;
                  const locked = n > 0 && !b.unlocked(g);
                  return (
                    <Pressable
                      key={level}
                      disabled={!n}
                      onPress={() => onSub(s, level)}
                      accessibilityLabel={`${levelName(b.rules, level)} ${b.nPassed(g)} of ${n}${locked ? ', locked' : ''}`}
                      style={{ width: 52, flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', gap: 2 }}>
                      {locked ? (
                        <MaterialCommunityIcons name="lock-outline" size={12} color={theme.colors.onSurfaceDisabled} />
                      ) : null}
                      <Text
                        variant="bodySmall"
                        style={{
                          fontVariant: ['tabular-nums'],
                          color: !n || locked ? theme.colors.onSurfaceDisabled : theme.colors.onSurface,
                        }}>
                        {n ? `${b.nPassed(g)}/${n}` : '·'}
                      </Text>
                    </Pressable>
                  );
                })}
              </Pressable>
            );
          })
        : null}
    </View>
  );
}
