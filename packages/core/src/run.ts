import type { CertRecord } from './certs';
import type { Catalog } from './courses';
import { examOutcome, examTitle, type ExamOutcome, type ExamPlan } from './exam';
import { isLessonItem, NEW_STEP, type LessonItem, type Queue } from './queue';
import { isoNow, makeAttempt } from './records';
import type { Result } from './result';
import { Board } from './schedule';
import { offersRaise, queueLine, type QueueCounts } from './screens';
import { newRecord } from './sync';
import type { AttemptRecord, Course, Question, RaiseRecord, SessionRecord, Status } from './types';

export type QueueItem = { q: Question; tag: Status; fresh: boolean; early: boolean } | { lesson: LessonItem };

/** What a client's copy holds when the run reads it: the catalog and every attempt stored so far. */
export interface QueueSource {
  catalog: Catalog | null;
  attempts: AttemptRecord[];
}

const attemptKey = (a: AttemptRecord) => `${a.t}|${a.course}|${a.id}`;

/**
 * A running queue, as both clients draw it. A method returns the record the client stores,
 * and the client re-renders from the fields after each call.
 */
export class QueueRun {
  current: QueueItem | null = null;
  done = false;
  results: Result[] = [];
  introduced = 0;
  shown = 0; // counts the picks, so a client keys each question's view on it
  // this queue's answers, so a pick never waits for the copy to catch up
  private mine: AttemptRecord[] = [];
  private stinted = false;

  readonly queue: Queue;
  readonly mode: SessionRecord['mode'];
  readonly course: string | null;
  readonly include: string | null;

  constructor(
    queue: Queue,
    mode: SessionRecord['mode'],
    course: string | null,
    include: string | null,
    src: QueueSource,
  ) {
    this.queue = queue;
    this.mode = mode;
    this.course = course;
    this.include = include;
    this.current = this.pick(src);
    this.done = !this.current;
  }

  board(src: QueueSource): Board | null {
    if (!src.catalog) return null;
    const known = new Set(src.attempts.map(attemptKey));
    const extra = this.mine.filter((a) => !known.has(attemptKey(a)));
    return Board.build(src.catalog, [...src.attempts, ...extra], this.course, this.include);
  }

  private pick(src: QueueSource, now = Date.now()): QueueItem | null {
    const b = this.board(src);
    const picked = b ? this.queue.pick(b, now) : null;
    this.shown++;
    if (!picked || !b) return null;
    if (isLessonItem(picked)) return { lesson: picked };
    return {
      q: picked,
      tag: b.status(picked, now),
      fresh: !b.attempts(picked).length,
      early: this.queue.early(b, picked, now),
    };
  }

  /** Records the answer to the current question, and returns the attempt to store. */
  answer(r: Result): AttemptRecord {
    const rec = makeAttempt(isoNow(), r.q.course, r.q.id, r.correct, r.guess, r.grade, r.card);
    this.mine.push(rec);
    this.results = [...this.results, r];
    if (this.current && 'q' in this.current && this.current.fresh) this.introduced++;
    return rec;
  }

  /** Moves to the next pick. The queue is done where nothing is left to serve. */
  next(src: QueueSource): void {
    this.current = this.pick(src);
    if (!this.current) this.done = true;
  }

  stop(): void {
    this.done = true;
  }

  /** The stint to store once the queue is done or left: once, and none where nothing was answered. */
  end(): SessionRecord | null {
    if (this.stinted || !this.results.length) return null;
    this.stinted = true;
    return newRecord.session(this.mode, this.score, this.results.length);
  }

  /** Raises today's limit, and reopens a queue that ended with nothing left. Returns the raise to store. */
  raise(src: QueueSource): RaiseRecord {
    this.queue.raise(NEW_STEP);
    if (!this.current) {
      const p = this.pick(src);
      if (p) {
        this.current = p;
        this.done = false;
        this.stinted = false;
      }
    }
    return newRecord.raise();
  }

  get score(): number {
    return this.results.filter((r) => r.correct).length;
  }

  /** The counts line, whether a raise is offered, and the summary's inputs. */
  reading(src: QueueSource, now: number) {
    const b = this.board(src);
    const counts: QueueCounts = b
      ? {
          reviews: this.queue.reviews(b, now).length,
          learning: this.queue.stepping(b, now).count,
          newLeft: this.queue.newLeft(b, now),
        }
      : { reviews: 0, learning: 0, newLeft: 0 };
    const unseenLeft = !!b && this.queue.scope.some((q) => !b.attempts(q).length);
    return {
      counts,
      left: queueLine(counts),
      raise: offersRaise(this.mode, counts.newLeft, unseenLeft),
      summary: {
        answered: this.results.length,
        correct: this.score,
        introduced: this.introduced,
        stopped: !!this.current,
      },
    };
  }
}

export type ExamPhase = 'ask' | 'done' | 'review';

/** What an exam stores at its end, together. */
export interface ExamRecords {
  attempts: AttemptRecord[];
  session: SessionRecord;
  cert: CertRecord | null;
}

/** An exam's records as the lines a client stores, in order: the answers, the stint, then the certification's. */
export type ExamLine =
  | { kind: 'attempt'; record: AttemptRecord }
  | { kind: 'session'; record: SessionRecord }
  | { kind: 'cert'; record: CertRecord };

export function examLines(r: ExamRecords | null): ExamLine[] {
  if (!r) return [];
  return [
    ...r.attempts.map((record) => ({ kind: 'attempt' as const, record })),
    { kind: 'session' as const, record: r.session },
    ...(r.cert ? [{ kind: 'cert' as const, record: r.cert }] : []),
  ];
}

/** A running exam: the questions asked one by one, the results, and the missed ones read back. */
export class ExamRun {
  phase: ExamPhase = 'ask';
  index = 0;
  reviewAt = 0;
  results: Result[] = [];
  private stored = false;

  readonly plan: ExamPlan;
  private readonly courses: Course[];

  constructor(plan: ExamPlan, courses: Course[]) {
    this.plan = plan;
    this.courses = courses;
  }

  get total(): number {
    return this.plan.questions.length;
  }

  get question(): Question | undefined {
    return this.phase === 'ask' ? this.plan.questions[this.index] : undefined;
  }

  get last(): boolean {
    return this.index + 1 === this.total;
  }

  answer(r: Result): void {
    this.results = [...this.results, r];
  }

  /** The next question, or the end after the last. */
  next(): ExamRecords | null {
    if (this.index + 1 < this.total) {
      this.index++;
      return null;
    }
    return this.stop();
  }

  /** Ends the exam and returns its records to store, once; none where nothing was answered. */
  stop(): ExamRecords | null {
    this.phase = 'done';
    return this.end();
  }

  /** The records, as `stop` gives them, for a client leaving the exam without a press. */
  end(): ExamRecords | null {
    if (this.stored || !this.results.length) return null;
    this.stored = true;
    const out = examOutcome(this.plan, this.results, isoNow(), this.courses);
    return {
      attempts: out.attempts,
      session: newRecord.session(this.plan.mode, out.score, out.n),
      cert: out.cert ? newRecord.cert(out.cert) : null,
    };
  }

  /** The score, the topics and the missed results, as the summary and the review read them. */
  get outcome(): ExamOutcome {
    return examOutcome(this.plan, this.results, '', this.courses);
  }

  get reviewed(): Result | undefined {
    return this.phase === 'review' ? this.outcome.missed[this.reviewAt] : undefined;
  }

  get reviewLast(): boolean {
    return this.reviewAt + 1 === this.outcome.missed.length;
  }

  review(): void {
    this.reviewAt = 0;
    this.phase = this.outcome.missed.length ? 'review' : 'done';
  }

  /** The next missed question, or the summary after the last. */
  nextMissed(): void {
    if (this.reviewAt + 1 < this.outcome.missed.length) this.reviewAt++;
    else this.phase = 'done';
  }

  /** Leaves the review for the summary. */
  closeReview(): void {
    this.phase = 'done';
  }

  get title(): string {
    return examTitle(this.phase, this.index, this.total, this.reviewAt, this.outcome.missed.length);
  }
}
