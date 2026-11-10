import { levelName, subTitle, topicTitle } from './courses';
import type { Focus } from './focus';
import { NEW_STEP } from './queue';
import type { Board } from './schedule';
import type { Course, Group, Question, Rules } from './types';

// what a screen says, for every platform: a platform changes the look alone

type NextUp = NonNullable<ReturnType<Board['nextUp']>>;

/** "Topic › Sub · Level", or "Sub · Level" where the topic is named already. */
export function groupLabel(c: Course | undefined, rules: Rules, g: Pick<Group, 'topic' | 'sub' | 'level'>, withTopic = true): string {
  const where = withTopic ? `${topicTitle(c, g.topic)} › ${subTitle(c, g.sub)}` : subTitle(c, g.sub);
  return `${where} · ${levelName(rules, g.level)}`;
}

/** The line above a question: where it sits, its level, its kind and the queue's tag. */
export function questionHead(c: Course | undefined, rules: Rules, q: Question, tag: string, early = false): string {
  const t = early ? (tag ? `${tag} · learning step, early` : 'learning step, early') : tag;
  return `${groupLabel(c, rules, q)} · ${q.kind}${t ? ` · ${t}` : ''}`;
}

export interface NextUpView {
  title: string;
  detail: string | null;
  accessibilityLabel: string;
  next: NextUp | null;
}

/** A module's next step on Home: the group or lesson, its progress, and how many others are open. */
export function nextUpView(b: Board, c: Course): NextUpView {
  const next = b.nextUp(c);
  if (!next) return { title: 'All unlocked groups done', detail: null, accessibilityLabel: 'All unlocked groups done', next: null };
  const g = next.group;
  const open = b.frontier(c).length;
  const detail = `${topicTitle(c, g.topic)} · ${b.nPassed(g)}/${b.groupQuestions(g).length} passed${open > 1 ? ` · ${open - 1} more open` : ''}`;
  if (next.lesson) {
    return { title: `Next up: read “${next.lesson.title}”`, detail, accessibilityLabel: `Next up: read the lesson ${next.lesson.title}`, next };
  }
  const level = levelName(b.rules, g.level);
  return {
    title: `Next up: ${subTitle(c, g.sub)} · ${level}`,
    detail,
    accessibilityLabel: `Next up: practise ${subTitle(c, g.sub)} ${level}`,
    next,
  };
}

export interface QueueCounts {
  reviews: number;
  learning: number; // in a learning step and not due yet, which Continue serves early
  newLeft: number;
}

/** A count and its noun, singular for one: "1 review", "2 reviews". */
export function counted(n: number, one: string, many = `${one}s`): string {
  return `${n} ${n === 1 ? one : many}`;
}

const learningPart = (n: number) => (n ? `${n} learning · ` : '');

/** The counts under Home's Continue. A strict focus names itself, and its new count is the focus's. */
export function continueLine(n: QueueCounts, strict = false): string {
  return strict
    ? `Strict focus · ${counted(n.reviews, 'review')} · ${learningPart(n.learning)}${n.newLeft} new left`
    : `${counted(n.reviews, 'review')} · ${learningPart(n.learning)}${n.newLeft} new left today`;
}

/** The counts at the top of a running queue. */
export function queueLine(n: QueueCounts): string {
  return `${n.reviews} due · ${learningPart(n.learning)}${n.newLeft} new left today`;
}

/** A running queue offers today's raise where only the day's limit holds unseen questions back. */
export function offersRaise(mode: string, newLeft: number, unseenLeft: boolean): boolean {
  return mode !== 'review' && newLeft === 0 && unseenLeft;
}

export type EmptyAction = 'raise' | 'certs' | 'clear-focus';

export interface EmptyContinue {
  notice: string;
  action: { kind: EmptyAction; label: string } | null;
}

/** Why Continue has nothing to serve, and the one act that would change that. */
export function emptyContinue(o: { blocked: boolean; newLimit: number; focus: Focus | null }): EmptyContinue {
  if (o.blocked) {
    // the day's limit, not the content, emptied the queue
    return {
      notice: `Today's ${o.newLimit} new questions are done, and more are unlocked.`,
      action: { kind: 'raise', label: `+${NEW_STEP} new today` },
    };
  }
  if (o.focus?.cert) {
    return {
      notice: 'Nothing weak, due or new for the targeted certificate. See its requirements and exam.',
      action: { kind: 'certs', label: 'Certificates' },
    };
  }
  if (o.focus) return { notice: 'Nothing weak, due or new in the focus.', action: { kind: 'clear-focus', label: 'Clear focus' } };
  return { notice: 'Nothing due and nothing new unlocked. Open a module to start a queue there.', action: null };
}

const QUEUE_TITLE: Record<string, string> = { next: 'Continue', review: 'Review', drill: 'Filtered' };

/** A running queue's title, by its mode. */
export function queueTitle(mode: string): string {
  return QUEUE_TITLE[mode] ?? mode;
}

/** What a queue left once it stops: a stop the user pressed, or nothing more ready. */
export function queueSummary(o: { answered: number; correct: number; introduced: number; stopped: boolean }) {
  const accuracy = o.answered ? Math.round((100 * o.correct) / o.answered) : 0;
  return {
    title: o.stopped ? 'Stopped' : 'Nothing more ready',
    line: `Accuracy ${accuracy}% · ${o.introduced} new introduced`,
  };
}
