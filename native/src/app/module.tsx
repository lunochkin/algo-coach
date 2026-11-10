import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useMemo, useRef, useState } from 'react';
import { ScrollView, View, type LayoutChangeEvent } from 'react-native';
import {
  GestureDetector,
  usePanGesture,
  usePinchGesture,
  useSimultaneousGestures,
  useTapGesture,
} from 'react-native-gesture-handler';
import { Appbar, Button, Card, Chip, SegmentedButtons, Text, useTheme } from 'react-native-paper';
import { cancelAnimation, useSharedValue, withDecay } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  alsoNeeds,
  alsoNeedsLine,
  type Board,
  certPips,
  certStates,
  type CertStatus,
  certToOpen as openedCert,
  type Course,
  groupCell,
  layoutClusters,
  lessonPanelSub,
  lessonView,
  levelCounts,
  levelDots,
  levelLine,
  levelName,
  levels,
  lineage,
  MAP_DIMS,
  MAP_FIT,
  MAP_LEGEND,
  MAP_LESSONS,
  MAP_READ,
  mapLit,
  MODULE_ARCHIVE,
  MODULE_FOCUS_HERE,
  MODULE_FOCUSED,
  MODULE_GROUPS_TAB,
  MODULE_MAP_TAB,
  MODULE_MISSING,
  MODULE_PAUSE,
  MODULE_RESUME,
  MODULE_START,
  moduleMeta,
  noGraph,
  subTitle,
  summary,
  topicTitle,
  unlocksLabel,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { CertSheet, stateColor } from '@/ui/certs';
import { styles, tones } from '@/ui/common';
import { MapCanvas, NODE_H, NODE_W, type CertPip } from '@/ui/mapcanvas';
import { ModuleGroups } from '@/ui/groups';
import { useArchive, usePauseToggle } from '@/ui/pause';
import { useStartSheet, type Scope } from '@/ui/start';

const MIN_SCALE = 0.25;
const MAX_SCALE = 2.5;
const MAX_FLING = 6000; // pt/s

export default function ModuleScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const p = useLocalSearchParams<{ course?: string }>();
  const c = st.catalog?.courses.find((x) => x.slug === p.course);
  const [tab, setTab] = useState<'groups' | 'map'>('groups');
  const [lessonsOn, setLessonsOn] = useState(false); // ~190 lesson nodes clutter the map; opt in
  const withLessons = lessonsOn && !!c?.graph?.lessons.length;
  const { board } = st;
  // named explicitly, so a paused module reads and serves too
  const b = useMemo(() => (c ? board(c.slug) : null), [board, c]);
  const starter = useStartSheet();
  const pause = usePauseToggle();
  const archive = useArchive();
  const now = Date.now();
  const sum = useMemo(() => (b ? summary(b, now) : null), [b, now]);

  if (!c || !b || !sum) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
        <Appbar.Header>
          <Appbar.BackAction onPress={() => router.back()} />
          <Appbar.Content title="Module" />
        </Appbar.Header>
        <Text style={{ padding: 16 }}>{MODULE_MISSING}</Text>
      </View>
    );
  }
  const aimed = st.focus?.course === c.slug && !st.focus.cert && !st.focus.topic;
  const due = b.questions().filter((q) => b.toReview(q, now)).length;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={c.title} />
      </Appbar.Header>
      <View style={{ paddingHorizontal: 16, gap: 8, paddingBottom: 8 }}>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {moduleMeta(c.topics.length, due, c.paused)}
        </Text>
        <Text variant="bodySmall">
          {levelCounts(b, c)
            .filter((x) => x.total)
            .map((x) => `${x.name} ${x.passed}/${x.total}`)
            .join(' · ')}
        </Text>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {`${sum.mastered} mastered · ${sum.weak} weak · ${sum.soon} more due within 7 days`}
        </Text>
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Button mode="contained" compact icon="play" onPress={() => starter.open({ course: c.slug, topic: null, sub: null, level: null })}>
            {MODULE_START}
          </Button>
          <Button
            mode="outlined"
            compact
            icon="crosshairs-gps"
            disabled={aimed}
            onPress={() => void st.setFocus({ course: c.slug, topic: null, sub: null, strict: !!st.focus?.strict })}>
            {aimed ? MODULE_FOCUSED : MODULE_FOCUS_HERE}
          </Button>
          <Button mode="outlined" compact icon={c.paused ? 'play' : 'pause'} onPress={() => pause.ask(c)}>
            {c.paused ? MODULE_RESUME : MODULE_PAUSE}
          </Button>
          {c.paused ? (
            <Button mode="outlined" compact icon="archive-outline" onPress={() => archive.ask(c)}>
              {MODULE_ARCHIVE}
            </Button>
          ) : null}
        </View>
        <SegmentedButtons
          value={tab}
          onValueChange={(v) => setTab(v as 'groups' | 'map')}
          buttons={[
            { value: 'groups', label: MODULE_GROUPS_TAB, icon: 'table' },
            { value: 'map', label: MODULE_MAP_TAB, icon: 'graph-outline' },
          ]}
        />
      </View>
      {tab === 'groups' ? (
        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 24 }}>
          <ModuleGroups c={c} b={b} onStart={starter.open} />
        </ScrollView>
      ) : (
        <>
          {c.graph?.lessons.length ? (
            <View style={[styles.row, { paddingHorizontal: 16, paddingBottom: 4 }]}>
              <Chip
                icon={lessonsOn ? 'check' : 'book-open-variant'}
                selected={lessonsOn}
                onPress={() => setLessonsOn(!lessonsOn)}
                accessibilityLabel={lessonsOn ? 'Hide lessons' : 'Show lessons'}>
                {MAP_LESSONS}
              </Chip>
            </View>
          ) : null}
          {!c.graph ? (
            <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>
              {noGraph(c)}
            </Text>
          ) : (
            <CourseMap key={`${c.slug}:${withLessons}`} c={c} b={b} bottom={insets.bottom} withLessons={withLessons} />
          )}
        </>
      )}
      {starter.sheet}
      {pause.dialog}
      {archive.dialog}
    </View>
  );
}

function CourseMap(props: { c: Course; b: Board; bottom: number; withLessons: boolean }) {
  const { c, b, bottom, withLessons } = props;
  const st = useStore();
  const certState = useMemo(
    () => (c.certs ? certStates(b, c, st.catalog?.certExams ?? []) : new Map<string, CertStatus>()),
    [b, c, st.catalog],
  );
  const theme = useTheme();
  const tone = tones(theme.dark);
  const layout = useMemo(() => layoutClusters(c, c.graph!, MAP_DIMS, withLessons), [c, withLessons]);
  const { nodes, width, height } = layout;
  const at = useMemo(() => new Map(nodes.map((n) => [n.sub, n])), [nodes]);
  const lv = levels(b.rules);
  const [picked, setPicked] = useState<string | null>(null);
  const starter = useStartSheet();
  const titles = useMemo(
    () => new Map([...c.topics.map((t) => [t.slug, t.title] as const), ['all', c.title] as const]),
    [c],
  );
  // a certificate node stands for its scope's certified levels; a tap opens the next one to earn
  const pips = useMemo(() => {
    const out = new Map<string, CertPip[]>();
    for (const [sub, xs] of certPips(c, certState, nodes)) {
      out.set(sub, xs.map((x) => ({ letter: x.letter, color: stateColor(x.state, theme), filled: x.filled })));
    }
    return out;
  }, [c, certState, nodes, theme]);
  const certToOpen = (scope: string) => openedCert(c, certState, scope);
  const lit = useMemo(() => mapLit(c, layout, picked, st.focus), [c, layout, picked, st.focus]);

  const tx = useSharedValue(0);
  const ty = useSharedValue(0);
  const scale = useSharedValue(1);
  const view = useRef({ w: 0, h: 0 });
  const viewSize = useSharedValue({ w: 0, h: 0 });
  const placedOnce = useRef(false);

  const fit = useCallback(() => {
    const { w, h } = view.current;
    if (!w || !h) return;
    const s = Math.max(MIN_SCALE, Math.min(1, (w / width) * 0.95, (h / height) * 0.95));
    scale.value = s;
    tx.value = (w - width * s) / 2;
    ty.value = (h - height * s) / 2;
  }, [width, height, scale, tx, ty]);

  const onLayout = (e: LayoutChangeEvent) => {
    view.current = { w: e.nativeEvent.layout.width, h: e.nativeEvent.layout.height };
    viewSize.value = view.current;
    if (placedOnce.current) return;
    placedOnce.current = true;
    // Start on the first group with new work, at full size.
    const first = b.frontier(c)[0];
    const n = first ? at.get(first.sub) : undefined;
    if (!n) return fit();
    scale.value = 1;
    tx.value = view.current.w / 2 - (n.x + NODE_W / 2);
    ty.value = view.current.h / 3 - (n.y + NODE_H / 2);
  };

  const hit = useCallback(
    (x: number, y: number) => {
      const cx = (x - tx.value) / scale.value;
      const cy = (y - ty.value) / scale.value;
      // A few points of slack around each node: small nodes at low zoom are hard to hit exactly.
      const k = 8 / scale.value;
      const n = nodes.find((p) => cx >= p.x - k && cx <= p.x + NODE_W + k && cy >= p.y - k && cy <= p.y + NODE_H + k);
      // While a lineage is lit, dimmed nodes are background: tapping one only clears the selection.
      setPicked(n && (!lit || lit.has(n.sub)) ? n.sub : null);
    },
    [nodes, tx, ty, scale, lit],
  );

  // Pan moves by per-event deltas and pauses while a pinch runs, so the two never fight over the
  // position (a stale pan start made the map jump when fingers lifted). A gesture that included
  // a pinch does not fling: its release velocity is the fingers', not a swipe.
  const pinching = useSharedValue(false);
  const pinchStart = useSharedValue({ x: 0, y: 0, s: 1, fx: 0, fy: 0, k: 1 });
  const pinched = useSharedValue(false);
  const lastPointers = useSharedValue(0);
  const pan = usePanGesture({
    minDistance: 8, // Android touch slop: finger drift during a tap must not start a pan
    onBegin: () => {
      'worklet';
      // A touch stops a fling where it is.
      cancelAnimation(tx);
      cancelAnimation(ty);
      pinched.value = pinching.value;
      lastPointers.value = 0;
    },
    onUpdate: (e) => {
      'worklet';
      // The pan follows the midpoint of all fingers, which jumps when a finger lands or lifts:
      // move only on one-finger events that follow a one-finger event.
      const one = e.numberOfPointers === 1;
      const steady = one && lastPointers.value === 1;
      lastPointers.value = e.numberOfPointers;
      if (pinching.value || !steady) return;
      tx.value += e.changeX;
      ty.value += e.changeY;
    },
    onDeactivate: (e) => {
      'worklet';
      if (pinched.value) return;
      // Glide on with the release velocity, like native scroll views, and bounce back at the
      // bounds: at least half the view keeps showing the graph.
      const { w, h } = viewSize.value;
      const s = scale.value;
      const fling = (v: number) => Math.max(-MAX_FLING, Math.min(MAX_FLING, v));
      const glide = (velocity: number, view: number, size: number) =>
        withDecay({
          velocity: fling(velocity),
          deceleration: 0.998,
          clamp: [view / 2 - size * s, view / 2],
          rubberBandEffect: true,
          rubberBandFactor: 0.6,
        });
      tx.value = glide(e.velocityX, w, width);
      ty.value = glide(e.velocityY, h, height);
    },
  });
  const pinch = usePinchGesture({
    onFinalize: () => {
      'worklet';
      pinching.value = false;
    },
    onActivate: (e) => {
      'worklet';
      pinching.value = true;
      pinched.value = true;
      cancelAnimation(tx);
      cancelAnimation(ty);
      pinchStart.value = { x: tx.value, y: ty.value, s: scale.value, fx: e.focalX, fy: e.focalY, k: e.scale || 1 };
    },
    onUpdate: (e) => {
      'worklet';
      // A lifting finger sends a last one-finger update whose "midpoint" is that finger: ignore it.
      if (e.numberOfPointers !== 2) return;
      // The content point that was under the fingers' midpoint at the start stays under it:
      // zooming and two-finger dragging in one motion.
      const p0 = pinchStart.value;
      const s = Math.min(MAX_SCALE, Math.max(MIN_SCALE, (p0.s * e.scale) / p0.k));
      const k = s / p0.s;
      tx.value = e.focalX - (p0.fx - p0.x) * k;
      ty.value = e.focalY - (p0.fy - p0.y) * k;
      scale.value = s;
    },
  });
  const tap = useTapGesture({
    runOnJS: true,
    maxDistance: 10,
    maxDuration: 600,
    onActivate: (e) => hit(e.x, e.y),
  });
  const gestures = useSimultaneousGestures(pan, pinch, tap);

  // level dots need scheduling queries: computed once per board, not on every selection
  const dots = useMemo(() => {
    const color = { covered: tone.done, open: tone.open, locked: theme.colors.onSurfaceDisabled, empty: null };
    const out = new Map<string, (string | null)[]>();
    for (const [sub, xs] of levelDots(b, c, nodes)) out.set(sub, xs.map((x) => (x ? color[x] : null)));
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, b, c, theme.dark]);
  const sel = picked ? at.get(picked) : undefined;

  return (
    <View style={{ flex: 1 }}>
      <View style={[styles.row, { paddingHorizontal: 16, flexWrap: 'wrap' }]}>
        <Legend color={tone.done} label={MAP_LEGEND.covered} />
        <Legend color={tone.open} label={MAP_LEGEND.open} />
        <Legend color={theme.colors.onSurfaceDisabled} label={MAP_LEGEND.locked} />
        <Legend color={null} label={MAP_LEGEND.empty} />
        <View style={{ flex: 1 }} />
        <Button compact icon="fit-to-page-outline" onPress={fit} accessibilityLabel={MAP_FIT}>
          Fit
        </Button>
      </View>
      <GestureDetector gesture={gestures}>
        <View style={{ flex: 1, overflow: 'hidden' }} onLayout={onLayout} collapsable={false}>
          <MapCanvas
            nodes={nodes}
            edges={layout.edges}
            at={at}
            picked={picked}
            lit={lit}
            dots={dots}
            c={c}
            b={b}
            clusters={layout.clusters}
            titles={titles}
            outside={layout.outside}
            pips={pips}
            tx={tx}
            ty={ty}
            scale={scale}
          />
        </View>
      </GestureDetector>
      {sel?.kind === 'cert' && certToOpen(sel.topic) ? (
        <CertSheet
          c={c}
          b={b}
          id={certToOpen(sel.topic)!}
          states={certState}
          onClose={() => setPicked(null)}
          onPractice={starter.open}
        />
      ) : sel?.kind === 'lesson' ? (
        <LessonPanel c={c} b={b} slug={sel.sub.slice(7)} bottom={bottom} />
      ) : sel ? (
        <NodePanel c={c} b={b} sub={sel.sub} topic={sel.topic} bottom={bottom} onPractice={starter.open} />
      ) : null}
      {starter.sheet}
    </View>
  );
}

function Legend({ color, label }: { color: string | null; label: string }) {
  const theme = useTheme();
  return (
    <View style={[styles.row, { gap: 4, minHeight: 32 }]}>
      <View
        style={{
          width: 10,
          height: 10,
          borderRadius: 5,
          backgroundColor: color ?? 'transparent',
          borderWidth: 1.2,
          borderColor: color ?? theme.colors.outline,
        }}
      />
      <Text variant="labelSmall">{label}</Text>
    </View>
  );
}

/** Per-level progress with what blocks it, what the subtopic unlocks, and the start sheet. */

function NodePanel(props: {
  c: Course;
  b: Board;
  sub: string;
  topic: string;
  bottom: number;
  onPractice: (s: Scope) => void;
}) {
  const { c, b, sub, topic, bottom, onPractice } = props;
  const st = useStore();
  const aimed = st.focus?.course === c.slug && st.focus.sub === sub && !st.focus.cert;
  const theme = useTheme();
  const unlocks = unlocksLabel(c, sub);
  const outside = alsoNeeds(c, sub, topic);
  return (
    <Card mode="elevated" style={{ margin: 12, marginBottom: bottom + 12 }}>
      <Card.Title title={subTitle(c, sub)} subtitle={topicTitle(c, topic)} />
      <Card.Content style={{ gap: 2 }}>
        {levels(b.rules).map((level) => {
          const cell = groupCell(b, { course: c.slug, topic, sub, level });
          const color = cell.state === 'empty' ? theme.colors.onSurfaceVariant : theme.colors.onSurface;
          return (
            <Text key={level} variant="bodySmall" style={{ color }}>
              {levelLine(levelName(b.rules, level), cell.line)}
            </Text>
          );
        })}
        {outside.length ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
            {alsoNeedsLine(outside)}
          </Text>
        ) : null}
        {unlocks ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
            {unlocks}
          </Text>
        ) : null}
      </Card.Content>
      <Card.Actions>
        <Button
          icon="crosshairs-gps"
          disabled={aimed}
          onPress={() => void st.setFocus({ course: c.slug, topic, sub, strict: !!st.focus?.strict })}>
          {aimed ? MODULE_FOCUSED : MODULE_FOCUS_HERE}
        </Button>
        <Button
          mode="contained-tonal"
          icon="play"
          onPress={() => onPractice({ course: c.slug, topic, sub, level: null })}>
          {MODULE_START}
        </Button>
      </Card.Actions>
    </Card>
  );
}

/** A lesson as a book: a cover with a spine, outlined by its state (done / available / locked). */

/** A lesson's state, its pretest so far, what it needs and teaches, and a way to read it. */
function LessonPanel(props: { c: Course; b: Board; slug: string; bottom: number }) {
  const { c, b, slug, bottom } = props;
  const theme = useTheme();
  const v = lessonView(b, c, slug);
  if (!v) return null;
  return (
    <Card mode="elevated" style={{ margin: 12, marginBottom: bottom + 12 }}>
      <Card.Title title={v.title} subtitle={lessonPanelSub(v.state)} />
      <Card.Content style={{ gap: 2 }}>
        <Text variant="bodySmall">{v.teaches}</Text>
        {v.needs ? <Text variant="bodySmall">{v.needs}</Text> : null}
        {v.pretest ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {v.pretest}
          </Text>
        ) : null}
      </Card.Content>
      <Card.Actions>
        <Button
          mode="contained-tonal"
          icon="book-open-variant"
          onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug } })}>
          {MAP_READ}
        </Button>
      </Card.Actions>
    </Card>
  );
}

/** A certificate as a box filled with its state colour; title and coverage/retention below. */
