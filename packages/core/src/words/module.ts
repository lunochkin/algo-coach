// what the knowledge screens say about the module, for every platform: a
// platform changes the look alone, and reads each sentence from here
import { STATE_LABEL, type CertStatus } from '../certs';
import { subTitle, topicTitle } from '../courses';
import type { CellState } from '../module';
import { counted } from '../screens';
import type { Course } from '../types';

// a module's page
export const MODULE_MISSING = 'No module of that name is open: it may be archived.';
export const MODULE_START = 'Start';
export const MODULE_FOCUS_HERE = 'Focus here';
export const MODULE_FOCUS = 'Focus';
export const MODULE_FOCUSED = 'Focused';
export const MODULE_PAUSE = 'Pause';
export const MODULE_RESUME = 'Resume';
export const MODULE_ARCHIVE = 'Archive';
export const MODULE_GROUPS_TAB = 'Groups';
export const MODULE_MAP_TAB = 'Map';

export function moduleMeta(topics: number, due: number, paused: boolean): string {
  return `${counted(topics, 'topic')} · ${due} due · ${paused ? 'paused' : 'active'}`;
}

export const focusOn = (name: string) => `Focus on ${name}`;

export const startGroup = (sub: string, level: string, line: string) => `Start ${sub}, ${level}: ${line}`;

// the archive dialog
export const archiveTitle = (title: string) => `Archive ${title}?`;
export const ARCHIVE_BODY =
  'An archived module leaves the home and every queue. Its answers stay, and restoring it loses nothing.';
export const ARCHIVE_KEEP = 'Keep it';

// the map tab
export function noGraph(c: Pick<Course, 'title' | 'graphErrors'>): string {
  return c.graphErrors.length
    ? `The prerequisite graph of ${c.title} is invalid and ignored: ${c.graphErrors[0]}`
    : `${c.title} has no prerequisite graph.`;
}

export const MAP_LEGEND: Record<CellState, string> = {
  covered: 'covered',
  open: 'open',
  locked: 'locked',
  empty: 'no questions',
};
export const MAP_LESSONS = 'Lessons';
export const MAP_FIT = 'Fit the map';
export const MAP_READ = 'Read';

export const lessonNode = (state: string) => `lesson · ${state}`;
export const lessonPanelSub = (state: string) => `Lesson · ${state}`;
export const levelLine = (level: string, line: string) => `${level}: ${line}`;
export const alsoNeedsLine = (subs: string[]) => `Also needs: ${subs.join(', ')}`;

// the start sheet
export const START_LEVEL = 'Level';
export const START_KIND = 'Kind';
export const START_ALL = 'All';
export const START_ONLY_REVIEWS = 'Only reviews';
export const START_NOTE = 'A queue over what these choices leave. The focus stays where it is.';
export const START_NOTHING = 'Nothing ready here';

export function startTitle(c: Course, scope: { topic?: string | null; sub?: string | null }): string {
  return scope.sub ? subTitle(c, scope.sub) : scope.topic ? topicTitle(c, scope.topic) : c.title;
}

// the certifications page and a certification's conditions
export const CERTS_TITLE = 'Certifications';
export const CERTS_NOTE = 'Rings: coverage outside, retention inside. A certification opens on its conditions.';
export const CERTS_NONE = 'No module carries certifications yet.';
export const CERT_TO_COVER = 'To cover';
export const CERT_START = 'Start';
export const CERT_TAKE_EXAM = 'Take exam';
export const CERT_TARGET = 'Target';
export const CERT_UNTARGET = 'Untarget';

export function certCell(title: string, s: CertStatus): string {
  return `${title}: ${s.state === 'not_certified' ? `practice only, ${s.passed} of ${s.questions} passed` : STATE_LABEL[s.state]}`;
}

export const practiceShare = (s: Pick<CertStatus, 'passed' | 'questions'>) =>
  s.questions ? `${s.passed}/${s.questions}` : '—';

// the line under a module's title: what its questions hold now and soon
export const moduleSummary = (s: { mastered: number; weak: number; soon: number }) =>
  `${s.mastered} mastered · ${s.weak} weak · ${s.soon} more due within 7 days`;

// a level no scope certifies is practice alone, and its column says so
export function practiceLevel(c: Pick<Course, 'certs'>, level: number): boolean {
  return (c.certs?.certs ?? []).filter((x) => x.level === level).every((x) => !x.certified);
}
export const PRACTICE = '(practice)';
export const coverageShare = (coverage: number) => `${Math.round(coverage * 100)}%`;
