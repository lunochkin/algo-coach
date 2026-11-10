import { router, useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { BackHandler, Pressable, ScrollView, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Appbar, Button, Divider, Switch, Text, TextInput, TouchableRipple, useTheme } from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type AnswerRow,
  block,
  byTopic,
  cardLabel,
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
  ASK_REVEAL,
  ASK_SAID_ELSE,
  ASK_SAID_TRAP,
  ASK_TICK_RECALLED,
  ASK_TRAPS,
  askChoose,
  askSubmit,
  detailAccepted,
  DETAIL_NONE,
  DETAIL_YOU,
  DETAIL_YOUR_ANSWER,
  DETAIL_YOURS,
  detailsToggle,
  EXAM_DONE,
  examReviewMissed,
  examReviewNext,
  LESSON_STOP_KICKER,
  LESSON_STOP_LATER,
  LESSON_STOP_READ,
  QUEUE_ANSWERED,
  QUEUE_DONE,
  QUEUE_RAISE,
  QUEUE_STOP,
  queueLeft,
  answerResult,
  canSubmit,
  ExamRun,
  type ExamRecords,
  flipped,
  gradeResult,
  QueueRun,
  type QueueSource,
  togglePick,
  NEW_STEP,
} from '@algo-coach/core';
import { useStore, type ExamSession, type QueueSession } from '@/lib/store';
import { BottomBar, CodeBlock, styles } from '@/ui/common';

export default function Quiz() {
  const st = useStore();
  const [s] = useState(st.session);
  if (s && 'queue' in s) return <QueueQuiz s={s} />;
  return <ExamQuiz s={s} />;
}

/** A lesson served in the queue: read it, and its way back returns here, or go on without it. */
function LessonStop({ item, bottom, onNext }: { item: LessonItem; bottom: number; onNext: () => void }) {
  const st = useStore();
  const theme = useTheme();
  const read = !!st.catalog?.lessonsDone?.has(`${item.course.slug}:${item.lesson.slug}`);
  const open = () => router.push({ pathname: '/lesson', params: { course: item.course.slug, slug: item.lesson.slug } });
  return (
    <View style={{ flex: 1 }}>
      <View style={[styles.page, { flex: 1, justifyContent: 'center' }]}>
        <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
          {LESSON_STOP_KICKER}
        </Text>
        <Text variant="headlineSmall">{item.lesson.title}</Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {lessonStopNote(read)}
        </Text>
      </View>
      <BottomBar bottom={bottom} row>
        {read ? (
          <Button mode="contained" style={{ flex: 1 }} onPress={onNext}>
            {ASK_NEXT}
          </Button>
        ) : (
          <>
            <Button mode="text" onPress={onNext}>
              {LESSON_STOP_LATER}
            </Button>
            <Button mode="contained" icon="book-open-variant" style={{ flex: 1 }} onPress={open}>
              {LESSON_STOP_READ}
            </Button>
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
      <Appbar.Header>
        <Appbar.Action icon="close" onPress={quit} accessibilityLabel={QUEUE_STOP} />
        <Appbar.Content title={done ? QUEUE_DONE : queueTitle(s.mode)} />
        <Text variant="labelLarge" style={{ marginRight: 16 }}>{`${score}/${rs.length}`}</Text>
      </Appbar.Header>
      <View style={[styles.row, { paddingHorizontal: 16, minHeight: 40 }]}>
        <Text variant="labelMedium" style={{ flex: 1, color: theme.colors.onSurfaceVariant }}>
          {left}
        </Text>
        {reading.raise ? (
          <Button compact mode="text" onPress={moreNew} accessibilityLabel={`Allow ${NEW_STEP} more new questions`}>
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
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
          <View style={{ alignItems: 'center', paddingVertical: 24, gap: 4 }}>
            <Text variant="titleMedium">{summary.title}</Text>
            <Text variant="displayMedium">{`${rs.length}`}</Text>
            <Text variant="bodyMedium">{QUEUE_ANSWERED}</Text>
          </View>
          <Text variant="bodyLarge">{summary.line}</Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            {queueLeft(left)}
          </Text>
          <Button mode="contained" onPress={() => router.back()} style={{ marginTop: 16 }}>
            {QUEUE_DONE}
          </Button>
        </ScrollView>
      )}
    </View>
  );
}

function ExamQuiz({ s }: { s: ExamSession | null }) {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [run] = useState(() => (s ? new ExamRun(s, st.catalog?.courses ?? []) : null));
  const [, rerender] = useState(0);
  const changed = () => rerender((x) => x + 1);
  const phase = run?.phase;

  // the answers, the stint and a certification's record are stored together at the end
  const store = useCallback(
    async (records: ExamRecords | null) => {
      if (!records) return;
      for (const a of records.attempts) await st.record(a);
      await st.finishSession(records.session);
      if (records.cert) await st.recordCertExam(records.cert);
    },
    [st],
  );

  const quit = useCallback(async () => {
    if (!run) return router.back();
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

  if (!run) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
        <Appbar.Header>
          <Appbar.BackAction onPress={() => router.back()} />
          <Appbar.Content title="No session" />
        </Appbar.Header>
      </View>
    );
  }

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
      <Appbar.Header>
        <Appbar.Action icon="close" onPress={quit} accessibilityLabel={QUEUE_STOP} />
        <Appbar.Content title={run.title} />
        {phase !== 'ask' ? <Text variant="labelLarge" style={{ marginRight: 16 }}>{`${score}/${out.n}`}</Text> : null}
      </Appbar.Header>
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
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
          <View style={{ alignItems: 'center', paddingVertical: 24 }}>
            <Text variant="displayMedium">{`${score}/${out.n}`}</Text>
            <Text variant="titleMedium">{`${out.percent}%`}</Text>
          </View>
          {out.byTopic.map((t) => (
            <View key={t.topic} style={styles.row}>
              <Text variant="bodyLarge" style={{ flex: 1 }}>
                {t.title}
              </Text>
              <Text variant="bodyLarge">{`${t.score}/${t.n}`}</Text>
            </View>
          ))}
          {missed.length ? (
            <Button
              mode="contained-tonal"
              icon="eye-outline"
              style={{ marginTop: 16 }}
              onPress={() => {
                run.review();
                changed();
              }}
            >
              {examReviewMissed(missed.length)}
            </Button>
          ) : null}
          <Button mode="contained" onPress={() => router.back()} style={{ marginTop: 8 }}>
            {EXAM_DONE}
          </Button>
        </ScrollView>
      )}
    </View>
  );
}

function Head({ q, tag, early = false }: { q: Question; tag: string; early?: boolean }) {
  const theme = useTheme();
  const catalog = useStore().catalog;
  const course = catalog?.courses.find((c) => c.slug === q.course);
  return (
    <>
      <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant }}>
        {questionHead(course, catalog?.rules ?? DEFAULT_RULES, q, tag, early)}
      </Text>
      <Text variant="titleMedium" selectable>
        {block(q.prompt)}
      </Text>
      {q.code ? <CodeBlock code={q.code} /> : null}
    </>
  );
}

function Choices(props: { q: Question; order: number[]; picked: number[]; onToggle?: (pos: number) => void }) {
  const { q, order, picked, onToggle } = props;
  const theme = useTheme();
  const multi = q.answer.length > 1;
  return (
    <>
      {multi ? (
        <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
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
            style={{
              flexDirection: 'row',
              gap: 12,
              padding: 12,
              borderRadius: 12,
              borderWidth: 1,
              borderColor: on ? theme.colors.primary : theme.colors.outlineVariant,
              backgroundColor: on ? theme.colors.secondaryContainer : 'transparent',
            }}
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
  const [picked, setPicked] = useState<number[]>([]);
  const [text, setText] = useState('');
  const [guessing, setGuessing] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [recalled, setRecalled] = useState<Set<number>>(new Set());
  const [fell, setFell] = useState<Set<number>>(new Set());
  const [wrong, setWrong] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [details, setDetails] = useState(false);
  const multi = q.answer.length > 1;
  const reply = { text, picked, guessing };
  const ready = canSubmit(q, reply);

  const answer = (r: Result) => {
    onAnswered(r);
    // Exam: no feedback until the end.
    if (exam) onNext();
    else setResult(r);
  };
  const submit = () => answer(answerResult(q, order, reply));
  const gradeCardNow = () => answer(gradeResult(q, order, recalled, fell, wrong));
  const toggle = (pos: number) => setPicked(togglePick(picked, pos, multi));

  return (
    // Edge-to-edge Android no longer resizes the window for the keyboard; this keeps the input and bottom bar above it.
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1 }}>
      <ScrollView
        contentContainerStyle={[styles.page, { paddingBottom: bottom + 96 }]}
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
            onChangeText={setText}
            editable={!result}
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            style={{ fontFamily: 'monospace' }}
            onSubmitEditing={() => ready && !result && submit()}
          />
        ) : null}
        {q.format !== 'card' && !result ? (
          <View style={styles.row}>
            <Switch value={guessing} onValueChange={setGuessing} />
            <Text variant="bodyMedium" onPress={() => setGuessing(!guessing)}>
              {ASK_GUESSING}
            </Text>
          </View>
        ) : null}
        {q.format === 'card' && revealed ? (
          <View style={{ gap: 4 }}>
            <Text variant="titleSmall">{ASK_TICK_RECALLED}</Text>
            {q.key.map((point, i) => (
              <Tick
                key={i}
                label={`${i + 1}. ${block(point)}`}
                on={recalled.has(i)}
                disabled={!!result}
                onPress={() => setRecalled(flipped(recalled, i))}
              />
            ))}
            {q.traps.length ? (
              <>
                <Text variant="titleSmall" style={{ marginTop: 8 }}>
                  {ASK_TRAPS}
                </Text>
                {q.traps.map((trap, i) => (
                  <Tick
                    key={i}
                    label={block(trap)}
                    hint={ASK_SAID_TRAP}
                    on={fell.has(i)}
                    disabled={!!result}
                    onPress={() => setFell(flipped(fell, i))}
                  />
                ))}
              </>
            ) : null}
            <Tick label={ASK_SAID_ELSE} on={wrong} disabled={!!result} onPress={() => setWrong(!wrong)} />
          </View>
        ) : null}
        {result ? <Verdict r={result} /> : null}
        {result ? <DetailsToggle r={result} open={details} onToggle={() => setDetails(!details)} /> : null}
      </ScrollView>

      <BottomBar bottom={bottom} row>
        {result ? (
          <Button mode="contained" style={{ flex: 1 }} onPress={onNext}>
            {last ? 'Finish' : ASK_NEXT}
          </Button>
        ) : q.format === 'card' ? (
          revealed ? (
            <Button
              mode="contained"
              style={{ flex: 1 }}
              accessibilityLabel={`Grade: ${cardLabel(q.key.length, recalled, fell, wrong)}`}
              onPress={gradeCardNow}
            >
              {cardLabel(q.key.length, recalled, fell, wrong)}
            </Button>
          ) : (
            <Button mode="contained" style={{ flex: 1 }} onPress={() => setRevealed(true)}>
              {ASK_REVEAL}
            </Button>
          )
        ) : (
          <Button mode="contained" style={{ flex: 1 }} disabled={!ready} onPress={submit}>
            {askSubmit(exam, last)}
          </Button>
        )}
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
        <Button mode="contained" style={{ flex: 1 }} onPress={onNext}>
          {examReviewNext(last)}
        </Button>
      </BottomBar>
    </View>
  );
}

function Verdict({ r }: { r: Result }) {
  const theme = useTheme();
  const { head, explain, note } = verdictView(r);
  if (!head) return explain ? <Text variant="bodyMedium">{explain}</Text> : null;
  return (
    <View style={{ gap: 6 }}>
      <Text variant="titleMedium" style={{ color: head.correct ? theme.colors.primary : theme.colors.error }}>
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
  const theme = useTheme();
  return (
    <View style={{ gap: 4 }}>
      <Text variant="labelMedium" style={{ color: theme.colors.primary }}>
        {title}
      </Text>
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
        borderRadius: 8,
        padding: 6,
        backgroundColor: row.yours ? theme.colors.secondaryContainer : 'transparent',
      }}
    >
      <Text variant="bodyMedium" selectable>
        <Text style={{ color: row.ok ? theme.colors.primary : theme.colors.error }}>{`${row.mark} `}</Text>
        {row.label}
        {row.yours ? <Text style={{ color: theme.colors.tertiary }}>{DETAIL_YOURS}</Text> : null}
      </Text>
      {row.note ? (
        <Text variant="bodySmall" selectable style={{ color: theme.colors.onSurfaceVariant, marginLeft: 18 }}>
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
  const course = useStore().catalog?.courses.find((c) => c.slug === q.course);
  const answer = yourAnswer(r);
  const sections = detailSections(q);
  return (
    <View style={{ gap: 12 }}>
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
      {taughtBy(q, course).map((x) => (
        <Text
          key={x.slug}
          variant="labelLarge"
          accessibilityRole="link"
          onPress={() =>
            router.push({ pathname: '/lesson', params: { course: x.course, slug: x.slug, anchor: x.anchor } })
          }
          style={{ color: theme.colors.primary, paddingVertical: 8 }}
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
      style={{
        minHeight: 48,
        borderRadius: 12,
        paddingHorizontal: 12,
        paddingVertical: 8,
        justifyContent: 'center',
        backgroundColor: on ? theme.colors.secondaryContainer : theme.colors.surfaceVariant,
      }}
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
