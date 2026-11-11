import type { CertRecord } from './certs';
import type { Catalog } from './courses';
import { currentFocus, type Focus, type FocusRecord } from './focus';
import { learnerCatalog } from './home';
import { moduleOrder, type OrderRecord } from './order';
import { newPerDay, todayLimit } from './queue';
import { Board } from './schedule';
import { setting, type SettingRecord } from './settings';
import type { AttemptRecord, Course, LessonRecord, RaiseRecord, StatusRecord } from './types';

/** One user's log, a list per kind of record. */
export interface LearnerLog {
  attempts: AttemptRecord[];
  statuses: StatusRecord[];
  lessons: LessonRecord[];
  certs: CertRecord[];
  focuses: FocusRecord[];
  settings: SettingRecord[];
  raises: RaiseRecord[];
  orders: OrderRecord[];
}

export interface Learner {
  catalog: Catalog | null; // archived modules removed; none before the snapshot is read
  archived: Course[];
  focus: Focus | null;
  board: (only?: string | null, include?: string | null) => Board | null;
  newPerDay: number;
  examSize: number;
  /** Today's new-question limit at `now`: a raise ends at the day's rollover. */
  limitAt: (now: number) => number;
  order: string[];
  certExams: CertRecord[];
}

const KINDS: Record<string, keyof LearnerLog> = {
  attempt: 'attempts',
  status: 'statuses',
  lesson: 'lessons',
  cert: 'certs',
  focus: 'focuses',
  setting: 'settings',
  raise: 'raises',
  order: 'orders',
};

/** The log from learn's lines, each tagged with its kind; a kind the learner reads nothing from is dropped. */
export function learnerLog(lines: readonly { kind: string; line: unknown }[]): LearnerLog {
  const log: LearnerLog = {
    attempts: [],
    statuses: [],
    lessons: [],
    certs: [],
    focuses: [],
    settings: [],
    raises: [],
    orders: [],
  };
  for (const one of lines) {
    const key = KINDS[one.kind];
    if (key) (log[key] as unknown[]).push(one.line);
  }
  return log;
}

/** The learner over the snapshot, or over none yet: the settings, the limit and the order need no content. */
export function learnerView(raw: Catalog | null, log: LearnerLog): Learner {
  const { catalog, archived } = raw ? learnerCatalog(raw, log) : { catalog: null, archived: [] };
  return {
    catalog,
    archived,
    focus: catalog ? currentFocus(log.focuses, catalog) : null,
    board: (only, include = null) => (catalog ? Board.build(catalog, log.attempts, only, include) : null),
    newPerDay: newPerDay(log.settings),
    examSize: setting(log.settings, 'exam_size'),
    limitAt: (now) => todayLimit(log.settings, log.raises, now),
    order: moduleOrder(log.orders),
    certExams: log.certs,
  };
}
