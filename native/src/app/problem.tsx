import { router, useLocalSearchParams } from 'expo-router';
import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import { AppState, ScrollView, View } from 'react-native';
import { Appbar, Button, IconButton, SegmentedButtons, Text, TouchableRipple, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  CLOCK_PAUSE,
  CLOCK_PAUSED,
  CLOCK_RUNNING,
  CLOCK_START,
  clockState,
  described,
  editorOpening,
  END_KEEP,
  END_NOTE,
  END_TITLE,
  problemCards,
  problemTried,
  RESTORE_SOLVE,
  SITTING_END,
  SITTING_ENDED,
  sittingBack,
  sittingRefused,
  type Draft,
  visibilityMove,
  submitLabel,
  type components,
} from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { autoStarts, draftOf, keepDraft, pressed } from '@/lib/sitting';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { Loaded, styles, tones } from '@/ui/common';
import { CodeEditor, type EditorHandle } from '@/ui/editor';
import { Sheet } from '@/ui/sheet';
import type { Key } from '@/lib/keys';
import { KeyPad } from '@/ui/keys';
import { Markdown } from '@/ui/markdown';
import { ClaimSheet } from '@/ui/claim';
import { Badge } from '@/ui/rows';
import { ElapsedClock, SubmissionVerdict } from '@/ui/verdict';

type Sitting = components['schemas']['Sitting'];
type Served = components['schemas']['Served'];
type Carry = components['schemas']['Carry'];
type Submitted = components['schemas']['Submitted'];
type Moved = { sitting: Sitting | null; elapsedSec: number | null; at: number };

// the engine ends a sitting nothing has touched, and a solver thinking is
// practising, so an open screen reads the sitting again, well under the
// 45 minutes `log.md` ends an untouched one at
const TOUCH_MS = 10 * 60 * 1000;

/**
 * A problem's record and its statement, and the sitting on it: the statement
 * and the editor as two tabs, under one bar holding the clock. Reading the
 * statement mints nothing, and the first clock press or submission mints the
 * sitting, as `log.md` gives.
 */
export default function ProblemScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const {
    problem = '',
    technique,
    card,
  } = useLocalSearchParams<{ problem: string; technique?: string; card?: string }>();
  const picked = useEngine('/api/problems/{problem_id}', { problem_id: problem });
  const listed = useEngine('/api/cards');
  const error = picked.error ?? listed.error;
  const [now] = useState(() => Date.now());
  const record = picked.data;
  const cards = record ? problemCards(listed.data ?? [], record.techniques, technique ?? null) : [];
  const muted = { color: theme.colors.onSurfaceVariant };

  const facts = record ? (
    <>
      <View style={[styles.row, { flexWrap: 'wrap' }]}>
        {record.difficulty ? <Badge label={record.difficulty} /> : null}
        <Text variant="bodySmall" style={muted}>
          {record.techniques.join(' · ')}
        </Text>
        <Text variant="bodySmall" style={muted}>
          {problemTried(record, now)}
        </Text>
      </View>
      {cards.length > 0 ? (
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Text variant="bodySmall" style={muted}>
            {cards.length === 1 ? 'Card:' : 'Cards:'}
          </Text>
          {cards.map((one) => (
            <TouchableRipple
              key={one.slug}
              accessibilityRole="link"
              onPress={() => router.push({ pathname: '/card', params: { slug: one.slug } })}
            >
              <Text variant="bodySmall" style={{ color: theme.colors.primary }}>
                {one.title}
              </Text>
            </TouchableRipple>
          ))}
        </View>
      ) : null}
    </>
  ) : null;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={record?.title ?? 'The problem'} />
      </Appbar.Header>
      {error || !record || listed.data === null ? (
        <View style={styles.page}>
          <Loaded
            of="the problem"
            state={{
              data: null,
              error,
              reload: () => {
                picked.reload();
                listed.reload();
              },
            }}
          >
            {() => null}
          </Loaded>
        </View>
      ) : record.retired ? (
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
          {facts}
          <Text variant="bodyMedium">
            This problem was retired: its statement asked for something its cases do not decide. It is served to nobody,
            and your attempts on it stay in your log.
          </Text>
        </ScrollView>
      ) : (
        <SittingOn
          problemId={problem}
          card={card ?? null}
          drilled={technique ?? null}
          facts={facts}
          bottom={insets.bottom}
        />
      )}
    </View>
  );
}

function SittingOn({
  problemId,
  card,
  drilled,
  facts,
  bottom,
}: {
  problemId: string;
  card: string | null;
  // the technique the claim answers for: the card's own, or the pick's
  drilled: string | null;
  facts: ReactNode;
  bottom: number;
}) {
  const theme = useTheme();
  const { origin, device } = useStore().settings;
  // the statement comes with the sitting running on the problem, where one runs
  const served = useEngine('/api/problems/{problem_id}/statement', { problem_id: problemId });
  const [carry, setCarry] = useState<Carry | null | undefined>(undefined);
  // the draft as the screen opened, read once: the editor seeds once
  const [kept, setKept] = useState<Draft | null | undefined>(undefined);
  useEffect(() => {
    void draftOf(problemId).then(setKept);
  }, [problemId]);
  // true where the app going to the background paused the sitting, so a pause
  // the user pressed is not resumed on return
  const byBackground = useRef(false);
  const [moved, setMoved] = useState<Moved | null>(null);
  const [moving, setMoving] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [submitted, setSubmitted] = useState<Submitted | null>(null);
  const [tab, setTab] = useState<'statement' | 'code'>('statement');
  const [keys, setKeys] = useState(true);
  const [ending, setEnding] = useState(false);
  // the claim is asked once the sitting ends on this screen, and answering it
  // or closing it leaves the screen where it is
  const [claimed, setClaimed] = useState(false);
  // set by the restore press, and kept with the draft so a reopened screen keeps it
  const restored = useRef<boolean | null>(null);
  const editor = useRef<EditorHandle>(null);
  const onKey = useCallback((key: Key) => editor.current?.press(key), []);
  const [names, setNames] = useState<string[]>([]);
  const code = useRef<string | null>(null);

  // each reading of the statement is a reading of the sitting, stamped on arrival
  const statement: Served | null = served.data;
  useEffect(() => {
    if (statement) setMoved({ sitting: statement.sitting, elapsedSec: statement.elapsed_sec, at: performance.now() });
  }, [statement]);

  // what a new sitting may open on, bounded by the card's run where the
  // problem came from a card. A carry that failed opens on the signature
  useEffect(() => {
    let live = true;
    void (async () => {
      try {
        const { data } = await engine(origin, await getToken()).GET('/api/problems/{problem_id}/carry', {
          params: { path: { problem_id: problemId }, query: { card } },
        });
        if (live) setCarry(data ?? null);
      } catch {
        if (live) setCarry(null);
      }
    })();
    return () => {
      live = false;
    };
  }, [origin, problemId, card]);

  // the running sitting comes with the statement, so the first render already
  // names it, and the editor seeds from that sitting's own draft
  const current = moved?.sitting ?? statement?.sitting ?? null;
  const sittingId = current?.id ?? null;
  const clock = clockState(current);

  // the preference starts a clock the user has not, once per screen
  const autoStarted = useRef(false);
  const statementIn = statement !== null;
  useEffect(() => {
    if (!statementIn || !clock.unstarted || clock.ended || autoStarted.current) return;
    autoStarted.current = true;
    void autoStarts().then((on) => {
      if (on) void move('start', { quiet: true });
    });
    // `move` is a new closure on every render, and it reads `sittingId` alone
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statementIn, clock.unstarted, clock.ended]);

  // the clock counts the time on the problem, and an app in the background
  // is time away from it. Returning resumes only what the background paused
  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      const next = visibilityMove(clock, state !== 'active', byBackground.current);
      byBackground.current = next.pausedByHiding;
      if (next.move) void move(next.move, { quiet: true });
    });
    return () => sub.remove();
    // `move` is a new closure on every render, and it reads `sittingId` alone
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clock.unstarted, clock.paused, clock.ended, sittingId]);

  useEffect(() => {
    if (sittingId === null || clock.ended) return;
    const tick = setInterval(() => {
      if (AppState.currentState !== 'active') return;
      void (async () => {
        const { data } = await engine(origin, await getToken()).GET('/api/sittings/{sitting_id}', {
          params: { path: { sitting_id: sittingId } },
        });
        if (data) setMoved({ sitting: data.sitting, elapsedSec: data.elapsed_sec, at: performance.now() });
      })();
    }, TOUCH_MS);
    return () => clearInterval(tick);
  }, [origin, sittingId, clock.ended]);

  // the first clock press or submission mints the sitting it runs in, named
  // by the device it was minted on
  async function begun(): Promise<string | null> {
    if (sittingId !== null) return sittingId;
    const { data, error } = await engine(origin, await getToken()).POST('/api/problems/{problem_id}/sittings', {
      params: { path: { problem_id: problemId } },
      body: { device },
    });
    if (!data) {
      setRefused(described(error));
      return null;
    }
    setMoved({ sitting: data.sitting, elapsedSec: data.elapsed_sec, at: performance.now() });
    return data.sitting.id;
  }

  // a move the app took by itself says nothing to the user, so it reports no
  // refusal: the next reading of the sitting carries whatever happened
  async function move(to: 'start' | 'pause' | 'resume' | 'end', { quiet = false } = {}) {
    setMoving(true);
    if (!quiet) setRefused(null);
    try {
      const id = to === 'start' ? await begun() : sittingId;
      if (id === null) return;
      const client = engine(origin, await getToken());
      const params = { params: { path: { sitting_id: id } } };
      const { data, error } =
        to === 'start'
          ? await client.POST('/api/sittings/{sitting_id}/start', params)
          : to === 'pause'
            ? await client.POST('/api/sittings/{sitting_id}/pause', params)
            : to === 'resume'
              ? await client.POST('/api/sittings/{sitting_id}/resume', params)
              : await client.POST('/api/sittings/{sitting_id}/end', params);
      if (data) setMoved({ sitting: data.sitting, elapsedSec: data.elapsed_sec, at: performance.now() });
      else if (!quiet) setRefused(described(error));
    } catch (reason) {
      if (!quiet) setRefused(String(reason));
    } finally {
      setMoving(false);
    }
  }

  // the user's own press, which alone sets the clock preference
  function press(to: 'start' | 'pause' | 'resume') {
    void pressed(to);
    void move(to);
  }

  if (served.error || !statement || carry === undefined || kept === undefined)
    return (
      <View style={styles.page}>
        <Loaded of="the problem" state={{ data: null, error: served.error, reload: served.reload }}>
          {() => null}
        </Loaded>
      </View>
    );

  const opened = editorOpening(kept, sittingId, carry, statement.signature);
  const solve = carry?.solved_code ?? null;
  // the user's own act: a solve is never carried, so it returns only here
  function restore() {
    if (solve === null) return;
    restored.current = true;
    editor.current?.replace(solve);
  }

  async function submit() {
    if (running) return;
    setRunning(true);
    setRefused(null);
    try {
      const id = await begun();
      if (id === null) return;
      const { data, error } = await engine(origin, await getToken()).POST('/api/sittings/{sitting_id}/submissions', {
        params: { path: { sitting_id: id } },
        body: { code: code.current ?? opened.code, restored: restored.current ?? opened.restored },
      });
      if (data) {
        setSubmitted(data);
        // a solve ends the sitting
        setMoved({ sitting: data.sitting, elapsedSec: data.attempt.time_to_solve_sec ?? null, at: performance.now() });
      } else setRefused(described(error));
    } catch (reason) {
      setRefused(String(reason));
    } finally {
      setRunning(false);
    }
  }

  const toggleKeys = () => {
    setKeys(!keys);
    setTimeout(() => editor.current?.measure(), 100);
  };

  return (
    <View style={{ flex: 1, paddingBottom: bottom + 8 }}>
      {/* the sitting is run from one bar above both tabs: the clock is what
          the solver is watched by */}
      <View style={[styles.row, { paddingHorizontal: 12, paddingVertical: 4, gap: 8 }]}>
        {clock.running ? (
          <View
            accessibilityLabel={CLOCK_RUNNING}
            style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: tones(theme.dark).done }}
          />
        ) : null}
        {moved ? <ElapsedClock elapsedSec={moved.elapsedSec} receivedAt={moved.at} running={clock.running} /> : null}
        {clock.paused && !clock.ended ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {CLOCK_PAUSED}
          </Text>
        ) : null}
        <View style={{ flex: 1 }} />
        {clock.ended ? (
          <>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {SITTING_ENDED}
            </Text>
            <Button mode="contained" compact onPress={() => router.back()}>
              {sittingBack(card)}
            </Button>
          </>
        ) : (
          <>
            {/* one press for the clock: it starts a clock that never ran,
                resumes a paused one, and pauses a running one */}
            <Button
              mode="outlined"
              compact
              disabled={moving}
              onPress={() => press(clock.unstarted ? 'start' : clock.paused ? 'resume' : 'pause')}
            >
              {clock.unstarted || clock.paused ? CLOCK_START : CLOCK_PAUSE}
            </Button>
            <Button mode="outlined" compact disabled={moving || sittingId === null} onPress={() => setEnding(true)}>
              {SITTING_END}
            </Button>
          </>
        )}
      </View>
      {refused ? (
        <Text variant="bodySmall" style={{ color: theme.colors.error, paddingHorizontal: 12 }}>
          {sittingRefused(refused)}
        </Text>
      ) : null}
      <SegmentedButtons
        value={tab}
        onValueChange={(value) => setTab(value as 'statement' | 'code')}
        style={{ marginHorizontal: 12, marginVertical: 6 }}
        buttons={[
          { value: 'statement', label: 'Statement', icon: 'text-box-outline' },
          { value: 'code', label: 'Code', icon: 'code-tags' },
        ]}
      />
      {/* the editor stays mounted under the statement, so a tab switch keeps
          what was typed */}
      <ScrollView
        style={{ display: tab === 'statement' ? 'flex' : 'none' }}
        contentContainerStyle={[styles.page, { paddingTop: 4 }]}
      >
        {facts}
        <Markdown>{statement.statement}</Markdown>
      </ScrollView>
      <View style={{ flex: 1, display: tab === 'code' ? 'flex' : 'none' }}>
        <CodeEditor
          ref={editor}
          onNames={setNames}
          initial={opened.code}
          onChange={(typed) => {
            code.current = typed;
            void keepDraft(problemId, sittingId, typed, restored.current ?? opened.restored);
          }}
        />
        <View style={[styles.row, { paddingHorizontal: 8, paddingVertical: 6, gap: 8 }]}>
          <Button mode="contained" onPress={() => void submit()} disabled={running || clock.ended}>
            {submitLabel(running)}
          </Button>
          {/* quiet, and marked on the attempt: a solve typed over a restored
              one is not an independent solve */}
          {solve !== null && !clock.ended ? (
            <Button mode="text" compact onPress={restore}>
              {RESTORE_SOLVE}
            </Button>
          ) : null}
          <IconButton
            icon={keys ? 'keyboard-close' : 'keyboard'}
            accessibilityLabel={keys ? 'Hide the keyboard' : 'Show the keyboard'}
            style={{ marginLeft: 'auto' }}
            onPress={toggleKeys}
          />
        </View>
        {submitted ? (
          // the verdict sits under the editor: a failing case is read beside
          // the code that failed it
          <ScrollView style={{ flexGrow: 0, maxHeight: 220 }} contentContainerStyle={{ paddingHorizontal: 12 }}>
            <SubmissionVerdict submitted={submitted} />
          </ScrollView>
        ) : null}
        {keys && !clock.ended ? (
          <View style={{ paddingHorizontal: 8, paddingTop: 6 }}>
            <KeyPad lines names={names} onKey={onKey} />
          </View>
        ) : null}
      </View>
      {sittingId !== null ? (
        <ClaimSheet
          sittingId={sittingId}
          drilled={drilled}
          visible={clock.ended && !claimed}
          onDone={() => setClaimed(true)}
        />
      ) : null}
      <Sheet
        visible={ending}
        onDismiss={() => setEnding(false)}
        title={END_TITLE}
        note={END_NOTE}
        actions={
          <>
            <Button onPress={() => setEnding(false)}>{END_KEEP}</Button>
            <Button
              mode="contained"
              onPress={() => {
                setEnding(false);
                void move('end');
              }}
            >
              {SITTING_END}
            </Button>
          </>
        }
      />
    </View>
  );
}
