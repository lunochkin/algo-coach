import { router, useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useRef, useState } from 'react';
import { BackHandler, Pressable, ScrollView, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Appbar, Button, Divider, Switch, Text, TextInput, TouchableRipple, useTheme } from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type AnswerRow,
  type AttemptRecord,
  block,
  Board,
  byTopic,
  cardFields,
  cardLabel,
  choiceOrder,
  DEFAULT_RULES,
  detailSections,
  gradeChoice,
  hasAnswer,
  isLessonItem,
  isoNow,
  type LessonItem,
  lessonStopNote,
  LETTERS,
  makeAttempt,
  matchShort,
  NEW_STEP,
  offersRaise,
  type Question,
  questionHead,
  queueLine,
  queueSummary,
  queueTitle,
  type Result,
  splitGuess,
  type Status,
  taughtBy,
  verdictView,
  youLine,
  yourAnswer,
} from '@algo-coach/core';
import { useStore, type ExamSession, type QueueSession } from '@/lib/store';
import { BottomBar, CodeBlock, styles } from '@/ui/common';

type Phase = 'ask' | 'done' | 'review';

export default function Quiz() {
  const st = useStore();
  const [s] = useState(st.session);
  if (s && 'queue' in s) return <QueueQuiz s={s} />;
  return <ExamQuiz s={s} />;
}

type Current = { q: Question; tag: Status; fresh: boolean; early: boolean } | { lesson: LessonItem };

/** A lesson served in the queue: read it (the reader records Done), or go on without it. */
function LessonStop({ item, bottom, onNext }: { item: LessonItem; bottom: number; onNext: () => void }) {
  const st = useStore();
  const theme = useTheme();
  const read = !!st.catalog?.lessonsDone?.has(`${item.course.slug}:${item.lesson.slug}`);
  const open = () => router.push({ pathname: '/lesson', params: { course: item.course.slug, slug: item.lesson.slug } });
  return (
    <View style={{ flex: 1 }}>
      <View style={[styles.page, { flex: 1, justifyContent: 'center' }]}>
        <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
          New lesson
        </Text>
        <Text variant="headlineSmall">{item.lesson.title}</Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {lessonStopNote(read)}
        </Text>
      </View>
      <BottomBar bottom={bottom} row>
        {read ? (
          <Button mode="contained" style={{ flex: 1 }} onPress={onNext}>
            Next
          </Button>
        ) : (
          <>
            <Button mode="text" onPress={onNext}>
              Later
            </Button>
            <Button mode="contained" icon="book-open-variant" style={{ flex: 1 }} onPress={open}>
              Read
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
  const queue = s.queue;
  // Answers of this queue, so a pick never waits for the store to catch up.
  const mine = useRef<AttemptRecord[]>([]);
  const board = useCallback(() => {
    if (!st.catalog) return null;
    const known = new Set(st.attempts);
    const extra = mine.current.filter((r) => !known.has(r));
    return Board.build(st.catalog, [...st.attempts, ...extra], s.course, s.include ?? null);
  }, [st.catalog, st.attempts, s.course, s.include]);
  const pickOne = useCallback((): Current | null => {
    const b = board();
    const q = b ? queue.pick(b, Date.now()) : null;
    if (!q || !b) return null;
    if (isLessonItem(q)) return { lesson: q };
    const now = Date.now();
    return { q, tag: b.status(q, now), fresh: !b.attempts(q).length, early: queue.early(b, q, now) };
  }, [board, queue]);
  const [current, setCurrent] = useState(() => pickOne());
  const [count, setCount] = useState(0); // keys Ask, so each pick starts clean
  const [done, setDone] = useState(!current);
  const results = useRef<Result[]>([]);
  const introduced = useRef(0);
  const ended = useRef(false);

  const end = useCallback(async () => {
    if (ended.current) return;
    ended.current = true;
    const rs = results.current;
    await st.finishSession(rs.filter((r) => r.correct).length, rs.length);
    setDone(true);
  }, [st]);

  const quit = useCallback(async () => {
    if (!done) {
      await end();
      if (results.current.length) return;
    }
    router.back();
  }, [done, end]);

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
    const rec = makeAttempt(isoNow(), r.q.course, r.q.id, r.correct, r.guess, r.grade, r.card);
    mine.current.push(rec);
    void st.record(rec);
    results.current = [...results.current, r];
    if (current && 'q' in current && current.fresh) introduced.current++;
  };
  const next = () => {
    const p = pickOne();
    setCurrent(p);
    setCount((x) => x + 1);
    if (!p) void end();
  };
  const moreNew = () => {
    queue.raise(NEW_STEP);
    // today's limit, so Home and the next queue count the raise too
    void st.raiseNew();
    if (!current) {
      const p = pickOne();
      if (p) {
        ended.current = false;
        setDone(false);
        setCurrent(p);
        setCount((x) => x + 1);
      }
    } else setCount((x) => x);
  };

  const b = board();
  const now = Date.now();
  const due = b ? queue.reviews(b, now).length : 0;
  const newLeft = b ? queue.newLeft(b, now) : 0;
  const stepping = b ? queue.stepping(b, now).count : 0;
  const left = queueLine({ reviews: due, learning: stepping, newLeft });
  const unseenLeft = !!b && queue.scope.some((q) => !b.attempts(q).length);
  const rs = results.current;
  const score = rs.filter((r) => r.correct).length;
  const summary = queueSummary({ answered: rs.length, correct: score, introduced: introduced.current, stopped: !!current });

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Action icon="close" onPress={quit} accessibilityLabel="Stop" />
        <Appbar.Content title={done ? 'Done' : queueTitle(s.mode)} />
        <Text variant="labelLarge" style={{ marginRight: 16 }}>{`${score}/${rs.length}`}</Text>
      </Appbar.Header>
      <View style={[styles.row, { paddingHorizontal: 16, minHeight: 40 }]}>
        <Text variant="labelMedium" style={{ flex: 1, color: theme.colors.onSurfaceVariant }}>
          {left}
        </Text>
        {offersRaise(s.mode, newLeft, unseenLeft) ? (
          <Button compact mode="text" onPress={moreNew} accessibilityLabel={`Allow ${NEW_STEP} more new questions`}>
            {`+${NEW_STEP} new`}
          </Button>
        ) : null}
      </View>
      {!done && current && 'lesson' in current ? (
        <LessonStop item={current.lesson} bottom={insets.bottom} onNext={next} />
      ) : !done && current && 'q' in current ? (
        <Ask
          key={count}
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
            <Text variant="bodyMedium">answered</Text>
          </View>
          <Text variant="bodyLarge">{summary.line}</Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            {`Left: ${left}`}
          </Text>
          <Button mode="contained" onPress={() => router.back()} style={{ marginTop: 16 }}>
            Done
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
  const exam = true;
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>('ask');
  const [reviewAt, setReviewAt] = useState(0);
  const results = useRef<Result[]>([]);
  const ended = useRef(false);
  const [, rerender] = useState(0);

  const end = useCallback(async () => {
    if (ended.current) return;
    ended.current = true;
    const rs = results.current;
    // Exam attempts are recorded together at the end, as in the CLI.
    const t = isoNow();
    for (const r of rs) await st.record(makeAttempt(t, r.q.course, r.q.id, r.correct, r.guess));
    const score = rs.filter((r) => r.correct).length;
    await st.finishSession(score, rs.length);
    if (s?.cert && rs.length) {
      // A certificate exam passes only when every question was answered and the score reaches the bar.
      const n = s.questions.length;
      const passed = rs.length === n && score >= s.cert.passShare * n;
      await st.recordCertExam({ course: s.cert.course, cert: s.cert.id, score, n, passed });
    }
    setPhase('done');
  }, [st]);

  const quit = useCallback(async () => {
    if (phase === 'review') return setPhase('done');
    if (phase === 'ask') {
      await end();
      if (results.current.length) return;
    }
    router.back();
  }, [phase, end]);

  useFocusEffect(
    useCallback(() => {
      const sub = BackHandler.addEventListener('hardwareBackPress', () => {
        void quit();
        return true;
      });
      return () => sub.remove();
    }, [quit]),
  );

  if (!s) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
        <Appbar.Header>
          <Appbar.BackAction onPress={() => router.back()} />
          <Appbar.Content title="No session" />
        </Appbar.Header>
      </View>
    );
  }

  const total = s.questions.length;
  const rs = results.current;
  const score = rs.filter((r) => r.correct).length;
  const missed = rs.filter((r) => !r.correct);

  const onAnswered = (r: Result) => {
    results.current = [...results.current, r];
    rerender((x) => x + 1);
  };
  const next = () => (index + 1 < total ? setIndex(index + 1) : void end());

  const title =
    phase === 'ask'
      ? `Exam · ${index + 1} / ${total}`
      : phase === 'review'
        ? `Missed ${reviewAt + 1} / ${missed.length}`
        : 'Done';

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Action icon="close" onPress={quit} accessibilityLabel="Quit exam" />
        <Appbar.Content title={title} />
        {phase !== 'ask' ? (
          <Text variant="labelLarge" style={{ marginRight: 16 }}>{`${score}/${rs.length}`}</Text>
        ) : null}
      </Appbar.Header>
      {phase === 'ask' ? (
        <Ask
          key={index}
          q={s.questions[index]}
          tag=""
          exam={exam}
          bottom={insets.bottom}
          onAnswered={onAnswered}
          onNext={next}
          last={index + 1 === total}
        />
      ) : phase === 'review' ? (
        <Reviewed
          key={reviewAt}
          r={missed[reviewAt]}
          bottom={insets.bottom}
          last={reviewAt + 1 === missed.length}
          onNext={() => (reviewAt + 1 < missed.length ? setReviewAt(reviewAt + 1) : setPhase('done'))}
        />
      ) : (
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
          <View style={{ alignItems: 'center', paddingVertical: 24 }}>
            <Text variant="displayMedium">{`${score}/${rs.length}`}</Text>
            <Text variant="titleMedium">
              {`${rs.length ? Math.round((100 * score) / rs.length) : 0}%`}
            </Text>
          </View>
          {byTopic(rs).map((t) => (
            <View key={t.topic} style={styles.row}>
              <Text variant="bodyLarge" style={{ flex: 1 }}>
                {t.topic}
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
                setReviewAt(0);
                setPhase('review');
              }}>
              {`Review missed (${missed.length})`}
            </Button>
          ) : null}
          <Button mode="contained" onPress={() => router.back()} style={{ marginTop: 8 }}>
            Done
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

function Choices(props: {
  q: Question;
  order: number[];
  picked: number[];
  onToggle?: (pos: number) => void;
}) {
  const { q, order, picked, onToggle } = props;
  const theme = useTheme();
  const multi = q.answer.length > 1;
  return (
    <>
      {multi ? (
        <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
          {`Choose ${q.answer.length}`}
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
            }}>
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

  const answer = (r: Result) => {
    onAnswered(r);
    // Exam: no feedback until the end.
    if (exam) onNext();
    else setResult(r);
  };

  const submit = () => {
    if (q.format === 'short') {
      const [reply, suffix] = splitGuess(text);
      answer({ q, correct: matchShort(reply, q), guess: guessing || suffix, order, picked: [], reply });
    } else {
      answer({ q, correct: gradeChoice(q, order, picked), guess: guessing, order, picked, reply: '' });
    }
  };

  const gradeCardNow = () => {
    const card = cardFields(q.key.length, recalled, fell, wrong);
    answer({ q, correct: card.grade === 'k', guess: false, order, picked: [], reply: '', grade: card.grade, card });
  };

  const toggle = (pos: number) => {
    if (!multi) setPicked([pos]);
    else setPicked(picked.includes(pos) ? picked.filter((p) => p !== pos) : [...picked, pos]);
  };

  const canSubmit = q.format === 'short' ? hasAnswer(text) : picked.length > 0;

  return (
    // Edge-to-edge Android no longer resizes the window for the keyboard; this keeps the input and bottom bar above it.
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1 }}>
      <ScrollView
        contentContainerStyle={[styles.page, { paddingBottom: bottom + 96 }]}
        keyboardShouldPersistTaps="handled">
        <Head q={q} tag={tag} early={early} />
        {q.format === 'choice' ? (
          <Choices q={q} order={order} picked={picked} onToggle={result ? undefined : toggle} />
        ) : null}
        {q.format === 'short' ? (
          <TextInput
            mode="outlined"
            label="Answer"
            value={text}
            onChangeText={setText}
            editable={!result}
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            style={{ fontFamily: 'monospace' }}
            onSubmitEditing={() => canSubmit && !result && submit()}
          />
        ) : null}
        {q.format !== 'card' && !result ? (
          <View style={styles.row}>
            <Switch value={guessing} onValueChange={setGuessing} />
            <Text variant="bodyMedium" onPress={() => setGuessing(!guessing)}>
              {"I'm guessing"}
            </Text>
          </View>
        ) : null}
        {q.format === 'card' && revealed ? (
          <View style={{ gap: 4 }}>
            <Text variant="titleSmall">Tick the points you recalled</Text>
            {q.key.map((point, i) => (
              <Tick
                key={i}
                label={`${i + 1}. ${block(point)}`}
                on={recalled.has(i)}
                disabled={!!result}
                onPress={() => setRecalled(flip(recalled, i))}
              />
            ))}
            {q.traps.length ? (
              <>
                <Text variant="titleSmall" style={{ marginTop: 8 }}>
                  Common wrong answers
                </Text>
                {q.traps.map((trap, i) => (
                  <Tick
                    key={i}
                    label={block(trap)}
                    hint="I said this"
                    on={fell.has(i)}
                    disabled={!!result}
                    onPress={() => setFell(flip(fell, i))}
                  />
                ))}
              </>
            ) : null}
            <Tick
              label="I also said something else wrong"
              on={wrong}
              disabled={!!result}
              onPress={() => setWrong(!wrong)}
            />
          </View>
        ) : null}
        {result ? <Verdict r={result} /> : null}
        {result ? <DetailsToggle r={result} open={details} onToggle={() => setDetails(!details)} /> : null}
      </ScrollView>

      <BottomBar bottom={bottom} row>
        {result ? (
          <Button mode="contained" style={{ flex: 1 }} onPress={onNext}>
            {last ? 'Finish' : 'Next'}
          </Button>
        ) : q.format === 'card' ? (
          revealed ? (
            <Button
              mode="contained"
              style={{ flex: 1 }}
              accessibilityLabel={`Grade: ${cardLabel(q.key.length, recalled, fell, wrong)}`}
              onPress={gradeCardNow}>
              {cardLabel(q.key.length, recalled, fell, wrong)}
            </Button>
          ) : (
            <Button mode="contained" style={{ flex: 1 }} onPress={() => setRevealed(true)}>
              Reveal
            </Button>
          )
        ) : (
          <Button mode="contained" style={{ flex: 1 }} disabled={!canSubmit} onPress={submit}>
            {exam ? (last ? 'Submit and finish' : 'Next') : 'Submit'}
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
          {last ? 'Back to results' : 'Next missed'}
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
        style={{ alignSelf: 'flex-start' }}>
        Details
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
      }}>
      <Text variant="bodyMedium" selectable>
        <Text style={{ color: row.ok ? theme.colors.primary : theme.colors.error }}>{`${row.mark} `}</Text>
        {row.label}
        {row.yours ? <Text style={{ color: theme.colors.tertiary }}>{'  ← you'}</Text> : null}
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
        <Section title="Your answer">
          {answer.kind === 'rows' ? (
            answer.rows.map((row) => <Row key={row.key} row={row} />)
          ) : (
            <Text variant="bodyMedium" selectable>
              {`You: ${answer.you}`}
              <Text style={{ color: theme.colors.onSurfaceVariant }}>{`  ·  accepted: ${answer.accepted}`}</Text>
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
          (no detail for this question yet)
        </Text>
      ) : null}
      {taughtBy(q, course).map((x) => (
        <Text
          key={x.slug}
          variant="labelLarge"
          accessibilityRole="link"
          onPress={() => router.push({ pathname: '/lesson', params: { course: x.course, slug: x.slug, anchor: x.anchor } })}
          style={{ color: theme.colors.primary, paddingVertical: 8 }}>
          {x.label}
        </Text>
      ))}
    </View>
  );
}

function flip(s: Set<number>, i: number): Set<number> {
  const next = new Set(s);
  if (next.has(i)) next.delete(i);
  else next.add(i);
  return next;
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
      }}>
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
