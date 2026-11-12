import { router, useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useReducer, useState } from 'react';
import { BackHandler, Pressable, ScrollView, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Button, Divider, type MD3Theme, Switch, Text, TextInput, TouchableRipple, useTheme } from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type AnswerRow,
  block,
  byTopic,
  choiceOrder,
  DEFAULT_RULES,
  detailSections,
  type LessonItem,
  lessonStopNote,
  LETTERS,
  type Question,
  questionHead,
  queueSummary,
  queueTitle,
  type Result,
  taughtBy,
  verdictView,
  youLine,
  yourAnswer,
  ASK_ANSWER,
  ASK_GUESSING,
  ASK_NEXT,
  ASK_SAID_ELSE,
  ASK_SAID_TRAP,
  ASK_TICK_RECALLED,
  ASK_TRAPS,
  askChoose,
  detailAccepted,
  DETAIL_NONE,
  DETAIL_YOU,
  DETAIL_YOUR_ANSWER,
  DETAIL_YOURS,
  detailsToggle,
  EXAM_DONE,
  examReviewMissed,
  examReviewNext,
  LESSON_STOP_LATER,
  LESSON_STOP_READ,
  QUEUE_ANSWERED,
  QUEUE_DONE,
  QUEUE_RAISE,
  QUEUE_STOP,
  queueLeft,
  examLines,
  ExamRun,
  type ExamRecords,
  QueueRun,
  type QueueSource,
  NEW_STEP,
  NO_SESSION,
  OF,
  EXAM_TITLE,
  raiseLabel,
  gradeLabel,
  askAct,
  askReducer,
  askResult,
  initialAsk,
  keyPointLabel,
  lessonStopKicker,
  lessonRead,
} from '@algo-coach/core';
import { EMPTY, type Edit, type Key, pressed } from '@/lib/keys';
import { useStore, type ExamSession, type QueueSession } from '@/lib/store';
import { Heading, PickPanel, PickRow } from '@/ui/rows';
import { BottomBar, CodeBlock, fromCopy, Loaded, Press, ScreenHeader, styles } from '@/ui/common';
import { KeyPad, PAD_HEIGHT } from '@/ui/keys';
import { font, palette, radius, space } from '@/ui/tokens';

// a note under an answer row starts past the row's mark and its space
const MARK_INDENT = 18;

export default function Quiz() {
  const st = useStore();
  const theme = useTheme();
  const [s] = useState(st.session);
  if (s && st.catalog) return 'queue' in s ? <QueueQuiz s={s} /> : <ExamQuiz s={s} />;
  const queue = !!s && 'queue' in s;
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={s && 'queue' in s ? queueTitle(s.mode) : s ? EXAM_TITLE : NO_SESSION} />
      <View style={styles.page}>
        <Loaded
          of={queue ? OF.queue : OF.exam}
          state={fromCopy(st, st.catalog ? { s } : null)}
          blank={NO_SESSION}
          blankWhen={(x) => !x.s}
        >
          {() => null}
        </Loaded>
      </View>
    </View>
  );
}

// a running queue's score, beside its title
function Score({ children }: { children: string }) {
  return (
    <Text variant="labelLarge" style={{ marginRight: space[4] }}>
      {children}
    </Text>
  );
}

/** A lesson served in the queue: read it, and its way back returns here, or go on without it. */
function LessonStop({ item, bottom, onNext }: { item: LessonItem; bottom: number; onNext: () => void }) {
  const st = useStore();
  const theme = useTheme();
  const read = lessonRead(st.catalog, item.course.slug, item.lesson.slug);
  const open = () => router.push({ pathname: '/lesson', params: { course: item.course.slug, slug: item.lesson.slug } });
  return (
    <View style={{ flex: 1 }}>
      <View style={[styles.page, { flex: 1, justifyContent: 'center' }]}>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {lessonStopKicker(item.course, item.lesson)}
        </Text>
        <Text variant="headlineSmall">{item.lesson.title}</Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {lessonStopNote(read)}
        </Text>
      </View>
      <BottomBar bottom={bottom} row>
        {read ? (
          <Press style={{ flex: 1 }} onPress={onNext}>
            {ASK_NEXT}
          </Press>
        ) : (
          <>
            <Press mode="text" onPress={onNext}>
              {LESSON_STOP_LATER}
            </Press>
            <Press icon="book-open-variant" style={{ flex: 1 }} onPress={open}>
              {LESSON_STOP_READ}
            </Press>
          </>
        )}
      </BottomBar>
    </View>
  );
}

/** A continuous queue: each question is picked when it is needed, from what is ready then. */
function QueueQuiz({ s }: { s: QueueSession }) {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const held = (): QueueSource => ({ catalog: st.catalog, attempts: st.attempts });
  const [run] = useState(() => new QueueRun(s.queue, s.mode, s.course, s.include ?? null, held()));
  const [, rerender] = useState(0);
  const changed = () => rerender((x) => x + 1);
  const done = run.done;

  const end = useCallback(async () => {
    await st.finishSession(run.end());
  }, [st, run]);

  // Stop reads the summary, a queue with nothing answered included; a second press leaves
  const quit = useCallback(async () => {
    if (done) return router.back();
    run.stop();
    changed();
    await end();
  }, [done, run, end]);

  useFocusEffect(
    useCallback(() => {
      const sub = BackHandler.addEventListener('hardwareBackPress', () => {
        void quit();
        return true;
      });
      return () => sub.remove();
    }, [quit]),
  );

  const onAnswered = (r: Result) => {
    void st.record(run.answer(r));
    changed();
  };
  const next = () => {
    run.next(held());
    changed();
    if (run.done) void end();
  };
  const moreNew = () => {
    // today's limit, so Home and the next queue count the raise too
    void st.raiseNew(run.raise(held()));
    changed();
  };

  const reading = run.reading(held(), Date.now());
  const { left } = reading;
  const current = run.current;
  const rs = run.results;
  const score = run.score;
  const summary = queueSummary(reading.summary);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader
        title={done ? QUEUE_DONE : queueTitle(s.mode)}
        back={{ onPress: quit, close: QUEUE_STOP }}
        aside={<Score>{`${score}/${rs.length}`}</Score>}
      />
      <View style={[styles.row, { paddingHorizontal: space[4], minHeight: 40 }]}>
        <Text variant="bodySmall" style={{ flex: 1, color: theme.colors.onSurfaceVariant }}>
          {left}
        </Text>
        {reading.raise ? (
          <Button compact mode="outlined" icon="plus" onPress={moreNew} accessibilityLabel={raiseLabel(NEW_STEP)}>
            {QUEUE_RAISE}
          </Button>
        ) : null}
      </View>
      {!done && current && 'lesson' in current ? (
        <LessonStop item={current.lesson} bottom={insets.bottom} onNext={next} />
      ) : !done && current && 'q' in current ? (
        <Ask
          key={run.shown}
          q={current.q}
          tag={current.tag}
          early={current.early}
          exam={false}
          bottom={insets.bottom}
          onAnswered={onAnswered}
          onNext={next}
          last={false}
        />
      ) : (
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 120 }]}>
          <View style={{ alignItems: 'center', paddingVertical: space[6], gap: space[1] }}>
            <Text variant="titleMedium">{summary.title}</Text>
            <Text variant="displayMedium">{`${rs.length}`}</Text>
            <Text variant="bodyMedium">{QUEUE_ANSWERED}</Text>
          </View>
          <Text variant="bodyLarge">{summary.line}</Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            {queueLeft(left)}
          </Text>
        </ScrollView>
      )}
      {done || !current ? (
        <BottomBar bottom={insets.bottom}>
          <Press onPress={() => router.back()}>{QUEUE_DONE}</Press>
        </BottomBar>
      ) : null}
    </View>
  );
}

function ExamQuiz({ s }: { s: ExamSession }) {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [run] = useState(() => new ExamRun(s, st.catalog?.courses ?? []));
  const [, rerender] = useState(0);
  const changed = () => rerender((x) => x + 1);
  const phase = run.phase;

  // the answers, the stint and a certification's record are stored together at the end
  const store = useCallback(
    async (records: ExamRecords | null) => {
      for (const line of examLines(records)) {
        if (line.kind === 'attempt') await st.record(line.record);
        else if (line.kind === 'session') await st.finishSession(line.record);
        else await st.recordCertExam(line.record);
      }
    },
    [st],
  );

  const quit = useCallback(async () => {
    if (phase === 'review') {
      run.closeReview();
      return changed();
    }
    if (phase === 'ask') {
      const records = run.stop();
      changed();
      return store(records);
    }
    router.back();
  }, [run, phase, store]);

  useFocusEffect(
    useCallback(() => {
      const sub = BackHandler.addEventListener('hardwareBackPress', () => {
        void quit();
        return true;
      });
      return () => sub.remove();
    }, [quit]),
  );

  const out = run.outcome;
  const { score, missed } = out;
  const q = run.question;
  const reviewed = run.reviewed;

  const onAnswered = (r: Result) => {
    run.answer(r);
    changed();
  };
  const next = () => {
    const records = run.next();
    changed();
    void store(records);
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader
        title={run.title}
        back={{ onPress: quit, close: QUEUE_STOP }}
        aside={phase !== 'ask' ? <Score>{`${score}/${out.n}`}</Score> : null}
      />
      {q ? (
        <Ask
          key={run.index}
          q={q}
          tag=""
          exam
          bottom={insets.bottom}
          onAnswered={onAnswered}
          onNext={next}
          last={run.last}
        />
      ) : reviewed ? (
        <Reviewed
          key={run.reviewAt}
          r={reviewed}
          bottom={insets.bottom}
          last={run.reviewLast}
          onNext={() => {
            run.nextMissed();
            changed();
          }}
        />
      ) : (
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 120 }]}>
          <View style={{ alignItems: 'center', paddingVertical: space[6] }}>
            <Text variant="displayMedium">{`${score}/${out.n}`}</Text>
            <Text variant="titleMedium">{`${out.percent}%`}</Text>
          </View>
          <PickPanel>
            {out.byTopic.map((t) => (
              <PickRow key={t.topic} title={t.title} stats={[{ label: '', value: `${t.score}/${t.n}` }]} />
            ))}
          </PickPanel>
        </ScrollView>
      )}
      {!q && !reviewed ? (
        <BottomBar bottom={insets.bottom} row>
          {missed.length ? (
            <Press
              mode="contained-tonal"
              icon="eye-outline"
              onPress={() => {
                run.review();
                changed();
              }}
            >
              {examReviewMissed(missed.length)}
            </Press>
          ) : null}
          <Press style={{ flex: 1 }} onPress={() => router.back()}>
            {EXAM_DONE}
          </Press>
        </BottomBar>
      ) : null}
    </View>
  );
}

function Head({ q, tag, early = false }: { q: Question; tag: string; early?: boolean }) {
  const theme = useTheme();
  const catalog = useStore().catalog;
  const course = catalog?.courses.find((c) => c.slug === q.course);
  return (
    <>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {questionHead(course, catalog?.rules ?? DEFAULT_RULES, q, tag, early)}
      </Text>
      <Text variant="titleMedium" selectable>
        {block(q.prompt)}
      </Text>
      {q.code ? <CodeBlock code={q.code} /> : null}
    </>
  );
}

// one option tile for a choice and a tick alike, as the web draws both: picked
// reads bordered in the primary and tinted
function optionTile(on: boolean, theme: MD3Theme) {
  return {
    minHeight: 48,
    padding: space[3],
    borderRadius: radius(theme).xl,
    borderWidth: 1,
    borderColor: on ? theme.colors.primary : theme.colors.outlineVariant,
    backgroundColor: on ? theme.colors.secondaryContainer : 'transparent',
  } as const;
}

function Choices(props: { q: Question; order: number[]; picked: number[]; onToggle?: (pos: number) => void }) {
  const { q, order, picked, onToggle } = props;
  const theme = useTheme();
  const multi = q.answer.length > 1;
  return (
    <>
      {multi ? (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {askChoose(q.answer.length)}
        </Text>
      ) : null}
      {order.map((i, pos) => {
        const on = picked.includes(pos);
        return (
          <Pressable
            key={pos}
            onPress={onToggle ? () => onToggle(pos) : undefined}
            accessibilityRole={multi ? 'checkbox' : 'radio'}
            accessibilityState={{ checked: on, disabled: !onToggle }}
            style={[optionTile(on, theme), { flexDirection: 'row', gap: space[3] }]}
          >
            <Text variant="titleSmall">{LETTERS[pos]}</Text>
            <Text variant="bodyLarge" style={{ flex: 1 }}>
              {q.choices[i]}
            </Text>
          </Pressable>
        );
      })}
    </>
  );
}

function Ask(props: {
  q: Question;
  tag: string;
  early?: boolean;
  exam: boolean;
  bottom: number;
  last: boolean;
  onAnswered: (r: Result) => void;
  onNext: () => void;
}) {
  const { q, tag, early, exam, bottom, last, onAnswered, onNext } = props;
  // Shuffle choices so position carries no information across sessions.
  const order = useMemo(() => choiceOrder(q.choices.length), [q]);
  const [edit, setEdit] = useState<Edit>(EMPTY);
  const onKey = useCallback((key: Key) => setEdit((was) => pressed(was, key)), []);
  const text = edit.text;
  // the answer's state and its one press, as core keeps them for every
  // platform; the reply's text lives in the app's keyboard state
  const [asked, dispatch] = useReducer(askReducer, undefined, initialAsk);
  const state = { ...asked, text };
  const { picked, guessing, revealed, recalled, fell, wrong, result } = state;
  const [details, setDetails] = useState(false);
  const multi = q.answer.length > 1;
  const press = askAct(q, state, exam ? { last } : null);
  const act = () => {
    if (press.act === 'next') return onNext();
    if (press.act === 'reveal') return dispatch({ type: 'reveal' });
    if (!press.enabled) return;
    const r = askResult(q, order, state);
    onAnswered(r);
    // Exam: no feedback until the end.
    if (exam) onNext();
    else dispatch({ type: 'answered', result: r });
  };
  const toggle = (pos: number) => dispatch({ type: 'pick', pos, multi });
  const padOpen = q.format === 'short' && !result;

  return (
    // Edge-to-edge Android no longer resizes the window for the keyboard; this keeps the input and bottom bar above it.
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1 }}>
      <ScrollView
        contentContainerStyle={[styles.page, { paddingBottom: bottom + 96 + (padOpen ? PAD_HEIGHT + 8 : 0) }]}
        keyboardShouldPersistTaps="handled"
      >
        <Head q={q} tag={tag} early={early} />
        {q.format === 'choice' ? (
          <Choices q={q} order={order} picked={picked} onToggle={result ? undefined : toggle} />
        ) : null}
        {q.format === 'short' ? (
          <TextInput
            mode="outlined"
            label={ASK_ANSWER}
            value={text}
            selection={edit.selection}
            onChangeText={(typed) => setEdit((was) => ({ ...was, text: typed }))}
            onSelectionChange={(e) => setEdit((was) => ({ ...was, selection: e.nativeEvent.selection }))}
            // the app's keyboard answers, and the system's never opens
            showSoftInputOnFocus={false}
            autoFocus
            editable={!result}
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            style={{ fontFamily: font.mono }}
            onSubmitEditing={() => press.act === 'submit' && act()}
          />
        ) : null}
        {q.format !== 'card' && !result ? (
          <View style={styles.row}>
            <Switch value={guessing} onValueChange={(on) => dispatch({ type: 'guess', on })} />
            <Text variant="bodyMedium" onPress={() => dispatch({ type: 'guess', on: !guessing })}>
              {ASK_GUESSING}
            </Text>
          </View>
        ) : null}
        {q.format === 'card' && revealed ? (
          <View style={{ gap: space[1] }}>
            <Heading sub title={ASK_TICK_RECALLED} />
            {q.key.map((point, i) => (
              <Tick
                key={i}
                label={keyPointLabel(i, block(point))}
                on={recalled.has(i)}
                disabled={!!result}
                onPress={() => dispatch({ type: 'recall', i })}
              />
            ))}
            {q.traps.length ? (
              <>
                <Heading sub title={ASK_TRAPS} />
                {q.traps.map((trap, i) => (
                  <Tick
                    key={i}
                    label={block(trap)}
                    hint={ASK_SAID_TRAP}
                    on={fell.has(i)}
                    disabled={!!result}
                    onPress={() => dispatch({ type: 'fall', i })}
                  />
                ))}
              </>
            ) : null}
            <Tick label={ASK_SAID_ELSE} on={wrong} disabled={!!result} onPress={() => dispatch({ type: 'wrong' })} />
          </View>
        ) : null}
        {result ? <Verdict r={result} /> : null}
        {result ? <DetailsToggle r={result} open={details} onToggle={() => setDetails(!details)} /> : null}
      </ScrollView>

      <BottomBar bottom={bottom} row above={padOpen ? <KeyPad onKey={onKey} /> : undefined}>
        <Press
          style={{ flex: 1 }}
          disabled={!press.enabled}
          accessibilityLabel={press.act === 'grade' ? gradeLabel(press.label) : undefined}
          onPress={act}
        >
          {press.label}
        </Press>
      </BottomBar>
    </KeyboardAvoidingView>
  );
}

/** A missed exam question: the learner's answer, the correct one, explain and details. */
function Reviewed({ r, bottom, last, onNext }: { r: Result; bottom: number; last: boolean; onNext: () => void }) {
  const theme = useTheme();
  const [details, setDetails] = useState(false);
  const q = r.q;
  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: bottom + 96 }]}>
        <Head q={q} tag="" />
        {q.format === 'choice' ? <Choices q={q} order={r.order} picked={r.picked} /> : null}
        <Text variant="titleSmall" style={{ color: theme.colors.tertiary }}>
          {youLine(r)}
        </Text>
        <Verdict r={r} />
        <DetailsToggle r={r} open={details} onToggle={() => setDetails(!details)} />
      </ScrollView>
      <BottomBar bottom={bottom} row>
        <Press style={{ flex: 1 }} onPress={onNext}>
          {examReviewNext(last)}
        </Press>
      </BottomBar>
    </View>
  );
}

function Verdict({ r }: { r: Result }) {
  const theme = useTheme();
  const { head, explain, note } = verdictView(r);
  if (!head) return explain ? <Text variant="bodyMedium">{explain}</Text> : null;
  return (
    <View style={{ gap: space[1.5] }}>
      <Text variant="titleMedium" style={{ color: head.correct ? palette(theme.dark).passed : theme.colors.error }}>
        {head.text}
      </Text>
      {explain ? (
        <Text variant="bodyMedium" selectable>
          {explain}
        </Text>
      ) : null}
      {note ? (
        <Text variant="bodyMedium" style={{ color: theme.colors.tertiary }}>
          {note}
        </Text>
      ) : null}
    </View>
  );
}

function DetailsToggle({ r, open, onToggle }: { r: Result; open: boolean; onToggle: () => void }) {
  return (
    <>
      <Divider />
      <Button
        mode="text"
        icon={open ? 'chevron-up' : 'chevron-down'}
        onPress={onToggle}
        style={{ alignSelf: 'flex-start' }}
      >
        {detailsToggle(open)}
      </Button>
      {open ? <Details r={r} /> : null}
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={{ gap: space[1] }}>
      <Heading sub title={title} />
      {children}
    </View>
  );
}

/** One row of the learner's answer, as `yourAnswer` gives it; `yours` highlights the learner's pick. */
function Row({ row }: { row: AnswerRow }) {
  const theme = useTheme();
  return (
    <View
      style={{
        borderRadius: radius(theme).lg,
        padding: space[1.5],
        backgroundColor: row.yours ? theme.colors.secondaryContainer : 'transparent',
      }}
    >
      <Text variant="bodyMedium" selectable>
        <Text style={{ color: row.ok ? palette(theme.dark).passed : theme.colors.error }}>{`${row.mark} `}</Text>
        {row.label}
        {row.yours ? <Text style={{ color: theme.colors.tertiary }}>{DETAIL_YOURS}</Text> : null}
      </Text>
      {row.note ? (
        <Text variant="bodySmall" selectable style={{ color: theme.colors.onSurfaceVariant, marginLeft: MARK_INDENT }}>
          {row.note}
        </Text>
      ) : null}
    </View>
  );
}

/** Your answer, then the detail's sections and the lessons teaching the question; empty ones omitted. */
function Details({ r }: { r: Result }) {
  const theme = useTheme();
  const q = r.q;
  const catalog = useStore().catalog;
  const course = catalog?.courses.find((c) => c.slug === q.course);
  const answer = yourAnswer(r);
  const sections = detailSections(q);
  return (
    <View style={{ gap: space[3] }}>
      {answer ? (
        <Section title={DETAIL_YOUR_ANSWER}>
          {answer.kind === 'rows' ? (
            answer.rows.map((row) => <Row key={row.key} row={row} />)
          ) : (
            <Text variant="bodyMedium" selectable>
              {`${DETAIL_YOU} ${answer.you}`}
              <Text style={{ color: theme.colors.onSurfaceVariant }}>{detailAccepted(answer.accepted)}</Text>
            </Text>
          )}
        </Section>
      ) : null}
      {sections.map((x) => (
        <Section key={x.title} title={x.title}>
          {'code' in x ? (
            <CodeBlock code={x.code} verbatim />
          ) : 'items' in x ? (
            x.items.map((p, i) => (
              <Text key={i} variant="bodyMedium" selectable>
                {`•  ${p}`}
              </Text>
            ))
          ) : (
            <Text variant="bodyMedium" selectable>
              {x.text}
            </Text>
          )}
        </Section>
      ))}
      {!answer && !sections.length ? (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {DETAIL_NONE}
        </Text>
      ) : null}
      {taughtBy(q, course, catalog?.lessonsDone).map((x) => (
        <Text
          key={x.slug}
          variant="labelLarge"
          accessibilityRole="link"
          onPress={() =>
            router.push({ pathname: '/lesson', params: { course: x.course, slug: x.slug, anchor: x.anchor } })
          }
          style={{ color: theme.colors.primary, paddingVertical: space[2] }}
        >
          {x.label}
        </Text>
      ))}
    </View>
  );
}

function Tick(props: { label: string; hint?: string; on: boolean; disabled: boolean; onPress: () => void }) {
  const { label, hint, on, disabled, onPress } = props;
  const theme = useTheme();
  return (
    <TouchableRipple
      onPress={onPress}
      disabled={disabled}
      borderless
      accessibilityRole="checkbox"
      accessibilityState={{ checked: on, disabled }}
      accessibilityLabel={hint ? `${hint}: ${label}` : label}
      style={[optionTile(on, theme), { justifyContent: 'center' }]}
    >
      <View style={styles.row}>
        <MaterialCommunityIcons
          name={on ? 'checkbox-marked' : 'checkbox-blank-outline'}
          size={24}
          color={on ? theme.colors.primary : theme.colors.onSurfaceVariant}
        />
        <View style={{ flex: 1 }}>
          <Text variant="bodyLarge" selectable>
            {label}
          </Text>
          {hint ? (
            <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {hint}
            </Text>
          ) : null}
        </View>
      </View>
    </TouchableRipple>
  );
}
