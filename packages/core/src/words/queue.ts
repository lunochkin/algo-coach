// what the knowledge screens say about the queue, for every platform: a
// platform changes the look alone, and reads each sentence from here
import { NEW_STEP } from '../queue';

// a running queue, and its summary
export const QUEUE_DONE = 'Done';
export const QUEUE_STOP = 'Stop';
export const QUEUE_RAISE = `+${NEW_STEP} new`;
export const QUEUE_ANSWERED = 'answered';
export const queueLeft = (line: string) => `Left: ${line}`;

// the lesson a queue stops on
export const LESSON_STOP_KICKER = 'New lesson';
export const LESSON_STOP_READ = 'Read';
export const LESSON_STOP_LATER = 'Later';

// one question
export const ASK_NEXT = 'Next';
export const ASK_SUBMIT = 'Submit';
export const ASK_REVEAL = 'Reveal';
export const ASK_ANSWER = 'Answer';
export const ASK_GUESSING = "I'm guessing";
export const ASK_TICK_RECALLED = 'Tick the points you recalled';
export const ASK_TRAPS = 'Common wrong answers';
export const ASK_SAID_TRAP = 'I said this';
export const ASK_SAID_ELSE = 'I also said something else wrong';
export const askChoose = (n: number) => `Choose ${n}`;

/** The answer's press: an exam moves on at once, and its last question finishes it. */
export function askSubmit(exam: boolean, last: boolean): string {
  if (!exam) return ASK_SUBMIT;
  return last ? 'Submit and finish' : ASK_NEXT;
}

// the verdict's detail
export const detailsToggle = (open: boolean) => (open ? 'Hide details' : 'Details');
export const DETAIL_YOUR_ANSWER = 'Your answer';
export const DETAIL_YOURS = ' ← you';
export const DETAIL_YOU = 'You:';
export const detailAccepted = (accepted: string) => ` · accepted: ${accepted}`;
export const DETAIL_NONE = 'No detail for this question yet.';

// a level exam's choices, its run and its results
export const EXAM_TITLE = 'Exam';
export const EXAM_NOTE = 'No feedback until the end.';
export const EXAM_MODULE = 'Module';
export const EXAM_ALL = 'All';
export const EXAM_LEVEL = 'Level';
export const EXAM_SIZE = 'Questions';
export const EXAM_DONE = 'Done';
export const EXAM_LOADING = 'Loading the exam…';
export const examFailed = (error: string) => `The exam did not load: ${error}`;
export const examReviewMissed = (n: number) => `Review missed (${n})`;
export const examReviewNext = (last: boolean) => (last ? 'Back to results' : 'Next missed');

// the lessons, and a lesson
export const LESSONS_TITLE = 'Lessons';
export const LESSONS_NONE = 'No module carries a lesson yet.';
export const aboutMinutes = (n: number) => `~${n} min`;

/** A lesson row's second line: its minutes where known, then what it teaches. */
export function lessonRowLine(minutes: number, teaches: string): string {
  return minutes ? `${aboutMinutes(minutes)} · ${teaches}` : teaches;
}

/** Under a lesson's title: its module, its minutes where the text is held, and whether it is read. */
export function lessonNote(module: string, minutes: number | null, read: boolean): string {
  return [module, minutes ? aboutMinutes(minutes) : null, read ? 'read' : null].filter(Boolean).join(' · ');
}

export const LESSON_MISSING = 'This lesson is not in the current modules.';
export const LESSON_NO_TEXT = "This lesson's text is not in the snapshot yet.";
export const LESSON_NEXT = 'Next';
export const LESSON_RELATED = 'Related';
export const LESSON_MARK_READ = 'Mark read';
export const LESSON_MARK_UNREAD = 'Mark unread';

// a paused module leaves exams unless the user names it, so its choice says so
export const examModuleChoice = (c: { title: string; paused?: boolean }) =>
  c.paused ? `${c.title} (paused)` : c.title;
