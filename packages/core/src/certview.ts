import { certStates, COURSE_SCOPE, STATE_LABEL, type CertRecord, type CertState, type CertStatus } from './certs';
import { levelName, subTitle } from './courses';
import type { Focus } from './focus';
import { bySavedOrder } from './order';
import type { Board } from './schedule';
import { counted } from './screens';
import type { Course } from './types';

/** One condition of a certification, held or not. */
export interface CertCheck {
  ok: boolean;
  text: string;
}

/** A certification's conditions as either client shows them, and what it offers. */
export interface CertConditions {
  title: string;
  state: CertState;
  label: string;
  note: string | null; // why a practice-only or a thin level is no certificate yet
  progressNote: string | null; // a locked certification's progress counts once it unlocks
  checks: CertCheck[];
  short: { sub: string; topic: string; line: string }[]; // the groups below coverage
  scope: string;
  targeted: boolean;
  offersTarget: boolean; // the focus can aim at it
  offersExam: boolean; // every other condition holds
}

const pct = (v: number) => `${Math.round(v * 100)}%`;
const held = (s: CertState | undefined) => s === 'earned' || s === 'needs_refresh' || s === 'empty';

export function certConditions(
  b: Board,
  c: Course,
  id: string,
  states: Map<string, CertStatus>,
  focus: Focus | null,
): CertConditions | null {
  const x = c.certs?.get(id);
  const status = states.get(id);
  if (!x || !status) return null;
  const note =
    status.state === 'not_certified'
      ? `This level is practice only: no certificate yet. So far ${status.passed}/${counted(status.questions, 'question')} passed. It becomes a certificate once the course enables it (when its question pool is ready).`
      : status.state === 'insufficient_pool'
        ? `Not enough questions yet for a fair exam: ${status.pool} available, ${Math.ceil(x.rule.minPoolRatio * x.rule.size)} needed (${x.rule.minPoolRatio}× the ${x.rule.size}-question exam). Until then it counts as not earned, so certificates that need it stay locked.`
        : null;
  const checks: CertCheck[] = (c.certs?.needs(id) ?? []).map((p) => {
    const s = states.get(p)?.state;
    const ok = held(s);
    return { ok, text: `Prerequisite: ${c.certs?.get(p)?.title ?? p}${ok ? '' : ` (${STATE_LABEL[s ?? 'locked'].toLowerCase()})`}` };
  });
  checks.push({ ok: status.short.length === 0, text: `Coverage: ${pct(status.coverage)} of ${counted(status.questions, 'question')} passed` });
  checks.push({
    ok: status.retention >= x.rule.share,
    text: `Retention: ${pct(status.retention)} stable ≥ ${x.rule.stabilityDays} days (needs ${pct(x.rule.share)})`,
  });
  if (x.rule.requireExam) {
    const last = status.lastExam;
    checks.push({
      ok: status.state === 'earned' || status.state === 'needs_refresh',
      text: last
        ? `Exam: last ${last.score}/${last.n} ${last.passed ? 'passed' : 'not passed'} (${last.t.slice(0, 10)})`
        : `Exam: ${counted(x.rule.size, 'question')}, pass ${pct(x.rule.passShare)}`,
    });
  }
  return {
    title: x.title,
    state: status.state,
    label: STATE_LABEL[status.state],
    note,
    progressNote: status.state === 'locked' ? 'Progress so far (counts once unlocked)' : null,
    checks,
    short: status.short.map((g) => ({ sub: g.sub, topic: g.topic, line: `${subTitle(c, g.sub)}: ${g.passed}/${g.total}` })),
    scope: `${levelName(b.rules, x.level)} · ${x.scope === COURSE_SCOPE ? 'whole course' : x.scope}`,
    targeted: focus?.cert === id,
    offersTarget: status.state !== 'earned' && status.state !== 'empty',
    offersExam: status.state === 'ready',
  };
}

/** The focus aiming at a certification: its topic, or the whole module. */
export function certFocus(c: Course, id: string, strict: boolean): Focus | null {
  const x = c.certs?.get(id);
  if (!x) return null;
  return { course: c.slug, topic: x.scope === COURSE_SCOPE ? null : x.scope, sub: null, strict, cert: x.id };
}

/** The first certification ready for its exam, in the user's module order, and the home's line naming it. */
export function readyCert(b: Board, order: string[], exams: CertRecord[]): { c: Course; id: string; line: string } | null {
  for (const c of bySavedOrder(b.courses, (x) => x.slug, order)) {
    if (!c.certs) continue;
    for (const [id, s] of certStates(b, c, exams)) {
      if (s.state === 'ready') return { c, id, line: `Ready for exam: ${c.certs.get(id)?.title ?? id}` };
    }
  }
  return null;
}
