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
import { Appbar, Button, Card, Chip, Text, useTheme } from 'react-native-paper';
import { cancelAnimation, useSharedValue, withDecay } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Board,
  certStates,
  type CertStatus,
  type Course,
  layoutClusters,
  levelName,
  levels,
  lineage,
  subTitle,
  topicTitle,
  unlocksLabel,
  bySavedOrder,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { CertSheet, stateColor } from '@/ui/certs';
import { styles, tones } from '@/ui/common';
import { MapCanvas, NODE_H, NODE_W, type CertPip } from '@/ui/mapcanvas';
import { useStartSheet, type Scope } from '@/ui/start';

const COL = 200;
const ROW = 74;
const MIN_SCALE = 0.25;
const MAX_SCALE = 2.5;
const MAX_FLING = 6000; // pt/s

export default function MapScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const courses = useMemo(
    () => bySavedOrder(st.catalog?.courses ?? [], (c) => c.slug, st.courseOrder),
    [st.catalog, st.courseOrder],
  );
  const p = useLocalSearchParams<{ course?: string }>();
  // a module row names its module, and otherwise the map opens on the focus
  const [course, setCourse] = useState(
    () => courses.find((c) => c.slug === (p.course ?? st.focus?.course))?.slug ?? courses[0]?.slug ?? '',
  );
  const c = courses.find((x) => x.slug === course);
  const [lessonsOn, setLessonsOn] = useState(false); // ~190 lesson nodes clutter the map; opt in
  const withLessons = lessonsOn && !!c?.graph?.lessons.length;
  const { board } = st;
  const b = useMemo(() => board(null), [board]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Map" />
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
      {c?.graph?.lessons.length ? (
        <View style={[styles.row, { paddingHorizontal: 16, paddingBottom: 4 }]}>
          <Chip
            icon={lessonsOn ? 'check' : 'book-open-variant'}
            selected={lessonsOn}
            onPress={() => setLessonsOn(!lessonsOn)}
            accessibilityLabel={lessonsOn ? 'Hide lessons' : 'Show lessons'}>
            Lessons
          </Chip>
        </View>
      ) : null}
      {!c || !b ? (
        <Text style={{ padding: 16 }}>No courses yet.</Text>
      ) : !c.graph ? (
        <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>
          {c.graphErrors.length
            ? `The prerequisite graph of ${c.title} is invalid and ignored: ${c.graphErrors[0]}`
            : `${c.title} has no prerequisite graph.`}
        </Text>
      ) : (
        <CourseMap key={`${c.slug}:${withLessons}`} c={c} b={b} bottom={insets.bottom} withLessons={withLessons} />
      )}
    </View>
  );
}

const DIMS = { nodeW: NODE_W, nodeH: NODE_H, col: COL, row: ROW, pad: 16, header: 32, gapX: 96, gapY: 40 };
const LETTERS = ['F', 'A', 'P', 'E'];

/** Subtopics upstream (`up`) or downstream of `start` in the real prerequisite graph. */
function reach(c: Course, start: string[], up: boolean): Set<string> {
  const out = new Set(start);
  const stack = [...start];
  while (stack.length) {
    const s = stack.pop()!;
    for (const [f, t] of c.graph?.edges ?? []) {
      const next = up ? (f === s ? t : null) : t === s ? f : null;
      if (next && !out.has(next)) {
        out.add(next);
        stack.push(next);
      }
    }
  }
  return out;
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
  const layout = useMemo(() => layoutClusters(c, c.graph!, DIMS, withLessons), [c, withLessons]);
  const { nodes, width, height } = layout;
  const at = useMemo(() => new Map(nodes.map((n) => [n.sub, n])), [nodes]);
  const lv = levels(b.rules);
  const [picked, setPicked] = useState<string | null>(null);
  const starter = useStartSheet();
  const titles = useMemo(
    () => new Map([...c.topics.map((t) => [t.slug, t.title] as const), ['all', c.title] as const]),
    [c],
  );
  // A certificate node stands for its scope's certified levels; a tap opens the next one to earn.
  const scopeCerts = useCallback(
    (scope: string) => (c.certs?.certs ?? []).filter((x) => x.scope === scope && x.certified),
    [c],
  );
  const pips = useMemo(() => {
    const out = new Map<string, CertPip[]>();
    for (const n of nodes) {
      if (n.kind !== 'cert') continue;
      out.set(
        n.sub,
        scopeCerts(n.topic).map((x) => {
          const state = certState.get(x.id)?.state ?? 'locked';
          return { letter: LETTERS[x.level], color: stateColor(state, theme), filled: state === 'earned' };
        }),
      );
    }
    return out;
  }, [nodes, scopeCerts, certState, theme]);
  const certToOpen = (scope: string): string | null => {
    const xs = scopeCerts(scope);
    const next = xs.find((x) => !['earned', 'empty'].includes(certState.get(x.id)?.state ?? ''));
    return (next ?? xs.at(-1))?.id ?? null;
  };
  // Lit: the picked node's real lineage across clusters, with the clusters and certificate nodes
  // it passes through; with nothing picked, a targeted certificate's scope.
  const lit = useMemo(() => {
    const around = (subs: Set<string>, extra: string[]) => {
      const out = new Set<string>([...subs, ...extra]);
      for (const s of subs) {
        const t = c.topics.find((x) => x.subs.includes(s))?.slug;
        if (t) out.add(`cluster:${t}`).add(`cert:${t}`);
      }
      return out;
    };
    if (picked?.startsWith('lesson:')) return lineage(layout.edges, picked);
    if (picked === 'cert:all') return null;
    if (picked?.startsWith('cert:')) {
      const own = c.topics.find((t) => t.slug === picked.slice(5))?.subs ?? [];
      return around(reach(c, own, true), [picked]);
    }
    if (picked) return around(new Set([...reach(c, [picked], true), ...reach(c, [picked], false)]), []);
    const f = st.focus;
    if (f?.cert && f.course === c.slug && f.scope) {
      return around(new Set([...f.scope].map((g) => g.slice(0, g.lastIndexOf('@')))), [`cert:${f.topic ?? 'all'}`]);
    }
    return null;
  }, [picked, layout, c, st.focus]);

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

  // Level dots need scheduling queries: compute them once per board, not on every selection.
  const dots = useMemo(() => {
    const out = new Map<string, (string | null)[]>();
    for (const n of nodes) {
      if (n.kind !== 'quiz') continue;
      out.set(
        n.sub,
        lv.map((level) => {
          const g = { course: c.slug, topic: n.topic, sub: n.sub, level };
          if (!b.groupQuestions(g).length) return null;
          return b.done(g) ? tone.done : b.unlocked(g) ? tone.open : theme.colors.onSurfaceDisabled;
        }),
      );
    }
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, b, c.slug, theme.dark]);
  const sel = picked ? at.get(picked) : undefined;

  return (
    <View style={{ flex: 1 }}>
      <View style={[styles.row, { paddingHorizontal: 16, flexWrap: 'wrap' }]}>
        <Legend color={tone.done} label="covered" />
        <Legend color={tone.open} label="open" />
        <Legend color={theme.colors.onSurfaceDisabled} label="locked" />
        <Legend color={null} label="no questions" />
        <View style={{ flex: 1 }} />
        <Button compact icon="fit-to-page-outline" onPress={fit} accessibilityLabel="Fit the map to the screen">
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
  // Prerequisites in other topics: the map draws them only as the certificate edge into the cluster.
  const outside = (c.graph?.needs(sub) ?? [])
    .map(([to]) => [to, c.topics.find((t) => t.subs.includes(to))?.slug] as const)
    .filter(([, t]) => t && t !== topic)
    .map(([to, t]) => `${to} (${t})`);
  return (
    <Card mode="elevated" style={{ margin: 12, marginBottom: bottom + 12 }}>
      <Card.Title title={subTitle(c, sub)} subtitle={topicTitle(c, topic)} />
      <Card.Content style={{ gap: 2 }}>
        {levels(b.rules).map((level) => {
          const g = { course: c.slug, topic, sub, level };
          const n = b.groupQuestions(g).length;
          const name = levelName(b.rules, level);
          const state = !n
            ? 'no questions'
            : b.done(g)
              ? `${b.nPassed(g)}/${n} · covered`
              : b.unlocked(g)
                ? `${b.nPassed(g)}/${n} · open`
                : `${b.nPassed(g)}/${n} · ${b.needsLabel(g)}`;
          return (
            <Text key={level} variant="bodySmall" style={{ color: n ? theme.colors.onSurface : theme.colors.onSurfaceVariant }}>
              {`${name}: ${state}`}
            </Text>
          );
        })}
        {outside.length ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
            {`Also needs: ${outside.join(', ')}`}
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
          {aimed ? 'Focused' : 'Focus here'}
        </Button>
        <Button
          mode="contained-tonal"
          icon="play"
          onPress={() => onPractice({ course: c.slug, topic, sub, level: null })}>
          Start
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
  const x = c.graph?.lesson(slug);
  if (!x) return null;
  const state = b.lessonState(c, x);
  const levelOf = (ref: string) => {
    const at = ref.lastIndexOf('@');
    return `${ref.slice(0, at)} · ${levelName(b.rules, Number(ref.slice(at + 1)))}`;
  };
  const needs = x.needs.map((r) => (r.startsWith('lesson:') ? `lesson ${c.graph?.lesson(r.slice(7))?.title ?? r}` : levelOf(r)));
  return (
    <Card mode="elevated" style={{ margin: 12, marginBottom: bottom + 12 }}>
      <Card.Title title={x.title} subtitle={`Lesson · ${state}`} />
      <Card.Content style={{ gap: 2 }}>
        <Text variant="bodySmall">{`Teaches: ${x.teaches.map(([s, l]) => `${s} · ${levelName(b.rules, l)}`).join(', ')}`}</Text>
        {needs.length ? <Text variant="bodySmall">{`Needs: ${needs.join(', ')}`}</Text> : null}
        {state !== 'done' ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {`Pretest: ${Math.min(b.tried(c, x), x.pretest)}/${x.pretest} questions tried`}
          </Text>
        ) : null}
      </Card.Content>
      <Card.Actions>
        <Button
          mode="contained-tonal"
          icon="book-open-variant"
          onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug } })}>
          Read
        </Button>
      </Card.Actions>
    </Card>
  );
}

/** A certificate as a box filled with its state colour; title and coverage/retention below. */
