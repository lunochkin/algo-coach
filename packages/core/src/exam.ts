import { certQuestions, type Cert, type CertRecord } from './certs';
import { levelName, topicTitle, type Catalog } from './courses';
import { examPool } from './modes';
import { makeAttempt } from './records';
import { validSetting } from './settings';
import type { Result } from './result';
import type { Board } from './schedule';
import { shuffle, type Rng } from './select';
import type { AttemptRecord, Course, Question, Rules } from './types';

/** An exam as both clients run it: a fixed sample, and for a certification's exam its bar. */
export interface ExamPlan {
  mode: string; // `exam-L<level>`, or `cert-<id>`: the stint's mode
  questions: Question[];
  cert?: { course: string; id: string; passShare: number };
}

/** A level exam: a uniform sample of every open group at the level, open questions left out. */
export function levelExam(b: Board, level: number, n: number, rng: Rng = Math.random): ExamPlan {
  return { mode: `exam-L${level}`, questions: shuffle(examPool(b, level), rng).slice(0, n) };
}

/** A certification's exam: a sample of its scope at its level, at the size its rule sets. */
export function certExam(b: Board, c: Course, id: string, rng: Rng = Math.random): ExamPlan | null {
  const x = c.certs?.get(id);
  if (!x) return null;
  const pool = certQuestions(b, c, x).filter((q) => q.format !== 'card');
  return {
    mode: `cert-${id}`,
    questions: shuffle(pool, rng).slice(0, x.rule.size),
    cert: { course: c.slug, id, passShare: x.rule.passShare },
  };
}

/** The level exam's press: how many it would ask of how many the level holds. */
export function levelExamLabel(rules: Rules, level: number, pool: number, n: number): string {
  return pool ? `Start (${Math.min(n, pool)} of ${pool})` : `No unlocked ${levelName(rules, level)} questions`;
}

// the size field is saved shortly after typing stops, on both clients
export const SIZE_SAVE_MS = 600;

/** A level exam's choice as it stands: the size typed, the level's pool, how many it asks, and its press. */
export interface LevelChoice {
  n: number;
  pool: number;
  count: number;
  label: string;
}

export function examChoice(b: Board | null, rules: Rules, level: number, sizeText: string): LevelChoice {
  const n = Number(sizeText);
  const pool = b ? examPool(b, level).length : 0;
  const count = validSetting('exam_size', n) ? Math.min(n, pool) : 0;
  return { n, pool, count, label: levelExamLabel(rules, level, pool, count) };
}

/** The size typed, where it is valid and differs from the standing one, so a save writes one record. */
export function sizeToSave(sizeText: string, stored: number): number | null {
  const n = Number(sizeText);
  return validSetting('exam_size', n) && n !== stored ? n : null;
}

/** A certification by its id, with the module that holds it. */
export function certById(
  catalog: Catalog | null | undefined,
  id: string | null | undefined,
): { c: Course; x: Cert } | null {
  if (!catalog || !id) return null;
  for (const c of catalog.courses) {
    const x = c.certs?.get(id);
    if (x) return { c, x };
  }
  return null;
}

/** An exam's title while it runs, while its misses are reviewed, and once it is done. */
export function examTitle(
  phase: 'ask' | 'review' | 'done',
  index: number,
  total: number,
  reviewAt: number,
  missed: number,
): string {
  if (phase === 'ask') return `Exam · ${index + 1} / ${total}`;
  if (phase === 'review') return `Missed ${reviewAt + 1} / ${missed}`;
  return 'Done';
}

/** What an exam leaves once it ends: its answers, stored together, its stint, and a certification's record. */
export interface ExamOutcome {
  score: number;
  n: number;
  percent: number;
  byTopic: { topic: string; title: string; score: number; n: number }[];
  missed: Result[];
  attempts: AttemptRecord[];
  cert: Omit<CertRecord, 't'> | null;
}

export function examOutcome(plan: ExamPlan, results: Result[], t: string, courses: Course[]): ExamOutcome {
  const score = results.filter((r) => r.correct).length;
  const topics = new Map<string, { topic: string; title: string; score: number; n: number }>();
  for (const r of results) {
    const key = `${r.q.course}/${r.q.topic}`;
    const c = courses.find((x) => x.slug === r.q.course);
    const e = topics.get(key) ?? { topic: key, title: topicTitle(c, r.q.topic), score: 0, n: 0 };
    e.score += r.correct ? 1 : 0;
    e.n += 1;
    topics.set(key, e);
  }
  const n = plan.questions.length;
  // a certification's exam passes only where every question was answered and the score reaches the bar
  const cert =
    plan.cert && results.length
      ? {
          course: plan.cert.course,
          cert: plan.cert.id,
          score,
          n,
          passed: results.length === n && score >= plan.cert.passShare * n,
        }
      : null;
  return {
    score,
    n: results.length,
    percent: results.length ? Math.round((100 * score) / results.length) : 0,
    byTopic: [...topics.values()],
    missed: results.filter((r) => !r.correct),
    // an exam stores its answers together at its end, at one moment
    attempts: results.map((r) => makeAttempt(t, r.q.course, r.q.id, r.correct, r.guess)),
    cert,
  };
}
