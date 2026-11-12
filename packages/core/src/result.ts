import { LETTERS } from './courses';
import { headings } from './lessontext';
import type { CardFields } from './records';
import { answerKey, block } from './reply';
import type { Course, Grade, Question } from './types';

/** One answered question as a result screen shows it, on either client. */
export interface Result {
  q: Question;
  correct: boolean;
  guess: boolean;
  order: number[]; // displayed position -> choice index
  picked: number[]; // displayed positions
  reply: string;
  grade?: Grade;
  card?: CardFields;
}

/** The learner's own reply, as a missed exam question repeats it. */
export function youLine(r: Result): string {
  const you =
    r.q.format === 'short'
      ? r.reply
      : [...r.picked]
          .sort((a, b) => a - b)
          .map((p) => LETTERS[p])
          .join('');
  return `You: ${you}${r.guess ? ' (guess)' : ''}`;
}

export interface VerdictView {
  // null on an open question, which the user graded: no verdict is the engine's
  head: { correct: boolean; text: string } | null;
  explain: string;
  note: string;
}

export function verdictView(r: Result): VerdictView {
  const q = r.q;
  const explain = q.explain ? block(q.explain) : '';
  if (q.format === 'card') return { head: null, explain, note: '' };
  const key = q.format === 'short' ? q.accept[0] : answerKey(q, r.order);
  const note =
    r.correct && r.guess
      ? 'Guessed: not counted as passed; it will come back.'
      : !r.correct && !r.guess
        ? 'Confidently wrong: a misconception. Details are worth it here.'
        : '';
  return { head: { correct: r.correct, text: r.correct ? '✓ Correct.' : `✗ Answer: ${key}.` }, explain, note };
}

/** One row of the learner's answer: a ✓, a ✗ or a · mark, a label, and what explains it. */
export interface AnswerRow {
  key: string;
  ok: boolean;
  mark: string;
  label: string;
  note: string;
  yours: boolean; // the learner picked it, or fell into it
}

export type YourAnswer = { kind: 'rows'; rows: AnswerRow[] } | { kind: 'short'; you: string; accepted: string } | null;

/** The "Your answer" section: each option's why, a typed reply, or an open question's ticks. */
export function yourAnswer(r: Result): YourAnswer {
  const q = r.q;
  const row = (key: string, ok: boolean, label: string, note = '', yours = false, mark?: string): AnswerRow => ({
    key,
    ok,
    mark: mark ?? (ok ? '✓' : '✗'),
    label,
    note: note ? block(note) : '',
    yours,
  });
  if (q.format === 'choice' && q.why.length) {
    const rows = r.order.map((i, pos) =>
      row(`o${pos}`, q.answer.includes(i), `${LETTERS[pos]}) ${q.why[i] ?? ''}`, '', r.picked.includes(pos)),
    );
    return { kind: 'rows', rows };
  }
  if (q.format === 'short') return { kind: 'short', you: r.reply, accepted: q.accept.join(', ') };
  if (q.format === 'card' && r.card) {
    const missed = new Set(r.card.missed ?? []);
    const fell = new Set(r.card.traps ?? []);
    const points = q.key.map((point, i) => row(`k${i}`, !missed.has(i), `${i + 1}. ${block(point)}`, q.keyDetail[i]));
    // the traps fallen into lead, so the misconception reads first
    const traps = [...q.traps.keys()]
      .sort((a, b) => Number(fell.has(b)) - Number(fell.has(a)))
      .map((i) =>
        row(
          `t${i}`,
          !fell.has(i),
          `${'abc'[i]}) ${block(q.traps[i])}`,
          q.trapsDetail[i],
          fell.has(i),
          fell.has(i) ? '✗' : '·',
        ),
      );
    return { kind: 'rows', rows: [...points, ...traps] };
  }
  return null;
}

/** One section of a question's detail. Code reads in monospace, and a diagram never wraps. */
export type DetailSection =
  | { title: 'Diagram' | 'Example'; code: string; wrap: boolean }
  | { title: 'How it works' | 'Versions'; text: string }
  | { title: 'Pitfalls'; items: string[] };

/** The detail's sections in reading order, each present only where the question carries it. */
export function detailSections(q: Question): DetailSection[] {
  const d = q.detail;
  if (!d) return [];
  const out: DetailSection[] = [];
  if (d.diagram) out.push({ title: 'Diagram', code: d.diagram, wrap: false });
  if (d.mechanism) out.push({ title: 'How it works', text: block(d.mechanism) });
  if (d.example) out.push({ title: 'Example', code: d.example, wrap: true });
  if (d.pitfalls.length) out.push({ title: 'Pitfalls', items: d.pitfalls.map(block) });
  if (d.versions) out.push({ title: 'Versions', text: block(d.versions) });
  return out;
}

export interface LessonLink {
  course: string;
  slug: string;
  anchor: string; // a section of the lesson, or '' for its start
  label: string;
  read: boolean;
}

/**
 * Where a question is taught: its own lesson, to the section it names, or
 * otherwise the lessons teaching its subtopic at its level. `done` holds the
 * read lessons as `course:lesson`.
 */
export function taughtBy(q: Question, c: Course | undefined, done?: ReadonlySet<string>): LessonLink[] {
  const graph = c?.graph;
  if (!graph) return [];
  const [slug, anchor = ''] = q.lesson.split('#');
  const own = q.lesson ? graph.lesson(slug) : undefined;
  if (own) {
    const part = anchor ? headings(c.lessonBodies[slug] ?? '')[anchor] : undefined;
    const read = isRead(own.slug);
    return [
      {
        course: q.course,
        slug: own.slug,
        anchor,
        label: `📖 Learn this: ${own.title}${part ? ` › ${part}` : ''}${read ? READ : ''}`,
        read,
      },
    ];
  }
  return graph.teaching(q.sub, q.level).map((x) => {
    const read = isRead(x.slug);
    return { course: q.course, slug: x.slug, anchor: '', label: `From lesson: ${x.title}${read ? READ : ''}`, read };
  });

  function isRead(slug: string): boolean {
    return !!done?.has(`${q.course}:${slug}`);
  }
}

// as a lesson's note says it: `lessonNote`
const READ = ' · read';
