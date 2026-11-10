import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AppState } from 'react-native';

import {
  attemptPath,
  Board,
  isoNow,
  learnerCatalog,
  sessionPath,
  statusPath,
  currentFocus,
  focusLine,
  focusPath,
  type Focus,
  type FocusRecord,
  type LessonRecord,
  lessonPath,
  certPath,
  type CertRecord,
  visibleCatalog,
  type Course,
  withStatuses,
  type CourseStatus,
  type StatusRecord,
  type AttemptRecord,
  type Catalog,
  type Question,
  type Queue,
  type SessionRecord,
  moduleOrder,
  orderPath,
  type OrderRecord,
  NEW_STEP,
  newPerDay,
  setting,
  SETTING_DEFAULT,
  settingPath,
  type SettingName,
  type SettingRecord,
  raisePath,
  type RaiseRecord,
  todayLimit,
} from '@algo-coach/core';

import { readCatalog } from './courses-cache';
import * as DB from './db';
import { cancelReminders, scheduleReminder } from './notify';
import { DEFAULTS, getToken, legacySettings, loadSettings, saveSettings, setToken, type Settings } from './settings';
import { signOut as signOutApp } from './auth';
import { SignedOut } from './engine';
import { syncOnce } from './sync';

export interface SyncState {
  running: boolean;
  lastAt: string | null;
  error: string | null;
}

/** A continuous queue (next, review, drill); `course` is the board selection picks use. */
export interface QueueSession {
  mode: 'next' | 'review' | 'drill';
  queue: Queue;
  course: string | null;
  include?: string | null; // a paused focus course, served anyway
}

/** An exam: a fixed sample, feedback at the end. */
export interface ExamSession {
  mode: string; // exam-L<level>, or cert-<id>
  questions: Question[];
  cert?: { course: string; id: string; passShare: number }; // a certificate exam
}

export type Session = QueueSession | ExamSession;

interface Store {
  ready: boolean;
  catalog: Catalog | null; // archived courses removed
  archived: Course[];
  attempts: AttemptRecord[];
  sessions: SessionRecord[];
  settings: Settings;
  // the study settings and today's raises are records, so every device reads one value
  newPerDay: number;
  examSize: number;
  setSetting: (name: SettingName, n: number) => Promise<void>;
  newLimit: number;
  // the user's module order, a record of the log, so every device lists the modules alike
  courseOrder: string[];
  setCourseOrder: (slugs: string[]) => Promise<void>;
  raiseNew: () => Promise<void>;
  hasToken: boolean;
  sync: SyncState;
  board: (only?: string | null, include?: string | null) => Board | null;
  requestSync: (delayMs?: number) => void;
  updateSettings: (s: Settings) => Promise<void>;
  signedIn: (token: string, user: string) => Promise<void>;
  // sends the outbox, then deletes this user's copy. Returns the records still unsent
  // instead, unless `force`, so the user decides whether they are lost
  signOut: (force: boolean) => Promise<number>;
  record: (rec: AttemptRecord) => Promise<void>;
  session: Session | null;
  setSession: (s: Session | null) => void;
  finishSession: (score: number, answered: number) => Promise<void>;
  setCourseStatus: (course: string, status: CourseStatus) => Promise<void>;
  focus: Focus | null;
  setFocus: (f: Focus | null) => Promise<void>;
  setLessonState: (course: string, lesson: string, status: LessonRecord['status']) => Promise<void>;
  recordCertExam: (rec: Omit<CertRecord, 't'>) => Promise<void>;
}

const Ctx = createContext<Store | null>(null);

export function useStore(): Store {
  const s = useContext(Ctx);
  if (!s) throw new Error('useStore outside StoreProvider');
  return s;
}

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [rawCatalog, setCatalog] = useState<Catalog | null>(null);
  const [statuses, setStatuses] = useState<StatusRecord[]>([]);
  const [focusRecords, setFocusRecords] = useState<FocusRecord[]>([]);
  const [lessonRecords, setLessonRecords] = useState<LessonRecord[]>([]);
  const [certRecords, setCertRecords] = useState<CertRecord[]>([]);
  // Pause state is learner data from status records, applied over the course snapshot.
  const learner = useMemo(
    () =>
      rawCatalog ? learnerCatalog(rawCatalog, { statuses, lessons: lessonRecords, certs: certRecords }) : null,
    [rawCatalog, statuses, lessonRecords, certRecords],
  );
  const archived = useMemo(() => learner?.archived ?? [], [learner]);
  const catalog = learner?.catalog ?? null;
  const focus = useMemo(
    () => (catalog ? currentFocus(focusRecords, catalog) : null),
    [catalog, focusRecords],
  );
  const [attempts, setAttempts] = useState<AttemptRecord[]>([]);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [settings, setSettings] = useState<Settings>(DEFAULTS);
  const [settingRecords, setSettingRecords] = useState<SettingRecord[]>([]);
  const [raises, setRaises] = useState<RaiseRecord[]>([]);
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [hasToken, setHasToken] = useState(false);
  const [sync, setSync] = useState<SyncState>({ running: false, lastAt: null, error: null });
  const [session, setSession] = useState<Session | null>(null);

  const settingsRef = useRef(settings);
  const userRef = useRef<string | null>(null);
  const catalogRef = useRef(rawCatalog);
  const statusesRef = useRef<StatusRecord[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const running = useRef(false);
  const retry = useRef<ReturnType<typeof setTimeout> | null>(null);
  const again = useRef(false);

  const reload = useCallback(async (withCatalog: boolean) => {
    const [a, s, ss, fs] = await Promise.all([
      DB.allAttempts(),
      DB.allSessions(),
      DB.allStatuses(),
      DB.allFocus(),
      DB.allLessons().then((ls) => {
        setLessonRecords(ls);
        return ls;
      }),
      DB.allCerts().then((cs) => {
        setCertRecords(cs);
        return cs;
      }),
      DB.allSettings().then(setSettingRecords),
      DB.allRaises().then(setRaises),
      DB.allOrders().then(setOrders),
    ]);
    setFocusRecords(fs);
    statusesRef.current = ss;
    setStatuses(ss);
    let cat: Catalog | null = null;
    if (withCatalog) {
      try {
        cat = await readCatalog();
        catalogRef.current = cat;
        setCatalog(cat);
      } catch (e) {
        setSync((x) => ({ ...x, error: `courses.json: ${String(e)}` }));
      }
    }
    setAttempts(a);
    setSessions(s);
    return { a, cat };
  }, []);

  const remind = useCallback(async (cat: Catalog | null, a: AttemptRecord[]) => {
    if (!cat) return;
    try {
      const b = Board.build(visibleCatalog(withStatuses(cat, statusesRef.current)), a);
      await scheduleReminder(b, settingsRef.current.reminderHour);
    } catch {
      // Reminders are best effort; a failure must not block sync or quizzes.
    }
  }, []);

  const runSync = useCallback(async () => {
    if (running.current) {
      again.current = true;
      return;
    }
    // Claim the slot before any await, or two syncs started together both get past the check.
    running.current = true;
    if (retry.current) clearTimeout(retry.current);
    retry.current = null;
    let failed = false;
    try {
      const token = await getToken();
      if (!token) {
        setSync((x) => ({ ...x, running: false, error: 'Not signed in: sign in from Settings' }));
        return;
      }
      setSync((x) => ({ ...x, running: true }));
      const r = await syncOnce(settingsRef.current, token, userRef.current);
      // a copy from before the owner was kept learns it from its first sync
      if (!userRef.current) await own(r.user, userRef);
      const lastAt = new Date().toISOString();
      await DB.setMeta('last_sync', lastAt);
      await DB.setMeta('last_error', '');
      const { a, cat } = await reload(r.coursesChanged);
      setSync({ running: false, lastAt, error: null });
      await remind(cat ?? catalogRef.current, a);
    } catch (e) {
      const error = e instanceof Error ? e.message : String(e);
      await DB.setMeta('last_error', error);
      setSync((x) => ({ ...x, running: false, error }));
      if (e instanceof SignedOut) {
        // revoked or expired on the engine: forget the token, and Home returns to Login.
        // The outbox keeps its records, which the next sign-in sends
        await setToken('');
        setHasToken(false);
      } else failed = true;
    } finally {
      running.current = false;
      if (again.current) {
        again.current = false;
        void runSync();
      } else if (failed) {
        retry.current = setTimeout(() => void runSync(), 30_000);
      }
    }
  }, [reload, remind]);

  const requestSync = useCallback(
    (delayMs = 0) => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => {
        timer.current = null;
        void runSync();
      }, delayMs);
    },
    [runSync],
  );

  useEffect(() => {
    void (async () => {
      userRef.current = (await DB.getMeta('user')) || null;
      DB.setOwner(userRef.current);
      const s = await loadSettings();
      setSettings(s);
      settingsRef.current = s;
      setHasToken(!!(await getToken()));
      const lastAt = await DB.getMeta('last_sync');
      const error = (await DB.getMeta('last_error')) || null;
      setSync({ running: false, lastAt, error });
      await movedSettings(s);
      await reload(true);
      setReady(true);
      requestSync(0);
    })();
    const sub = AppState.addEventListener('change', (st) => {
      if (st === 'active') requestSync(0);
    });
    return () => sub.remove();
  }, [reload, requestSync]);

  const board = useCallback(
    (only?: string | null, include: string | null = null) =>
      catalog ? Board.build(catalog, attempts, only, include) : null,
    [catalog, attempts],
  );

  const updateSettings = useCallback(async (s: Settings) => {
    await saveSettings(s);
    setSettings(s);
    settingsRef.current = s;
  }, []);

  const signedIn = useCallback(
    async (token: string, user: string) => {
      if (userRef.current !== user) await own(user, userRef);
      await setToken(token);
      setHasToken(true);
      await reload(false);
    },
    [reload],
  );

  const signOut = useCallback(
    async (force: boolean) => {
      const token = await getToken();
      if (token && !force) {
        try {
          await syncOnce(settingsRef.current, token, userRef.current);
        } catch {
          // counted below: what the outbox still holds is what sign-out would lose
        }
        const left = (await DB.pending()).length;
        if (left) return left;
      }
      if (token) await signOutApp(settingsRef.current.origin, token).catch(() => undefined);
      await DB.erase(userRef.current);
      await cancelReminders();
      await DB.setMeta('user', '');
      userRef.current = null;
      DB.setOwner(null);
      await setToken('');
      setHasToken(false);
      await reload(false);
      return 0;
    },
    [reload],
  );

  const record = useCallback(
    async (rec: AttemptRecord) => {
      await DB.addLocal('attempts', attemptPath(settingsRef.current.device, rec.t), rec);
      setAttempts((xs) => [...xs, rec]);
      requestSync(10_000);
    },
    [requestSync],
  );

  const setCourseStatus = useCallback(
    async (course: string, status: CourseStatus) => {
      const rec: StatusRecord = { t: isoNow(), course, status };
      await DB.addLocal('statuses', statusPath(settingsRef.current.device, rec.t), rec);
      statusesRef.current = [...statusesRef.current, rec];
      setStatuses(statusesRef.current);
      requestSync(0);
      await remind(catalogRef.current, await DB.allAttempts());
    },
    [requestSync, remind],
  );

  const setFocus = useCallback(
    async (f: Focus | null) => {
      const rec: FocusRecord = { t: isoNow(), ...focusLine(f) };
      await DB.addLocal('focus', focusPath(settingsRef.current.device, rec.t), rec);
      setFocusRecords((xs) => [...xs, rec]);
      // Quick toggles collapse into one upload; back-to-back writes of one file conflict on GitHub.
      requestSync(2000);
    },
    [requestSync],
  );

  const setLessonState = useCallback(
    async (course: string, lesson: string, status: LessonRecord['status']) => {
      const rec: LessonRecord = { t: isoNow(), course, lesson, status };
      await DB.addLocal('lessons', lessonPath(settingsRef.current.device, rec.t), rec);
      setLessonRecords((xs) => [...xs, rec]);
      requestSync(0);
    },
    [requestSync],
  );

  const recordCertExam = useCallback(
    async (rec: Omit<CertRecord, 't'>) => {
      const full: CertRecord = { t: isoNow(), ...rec };
      await DB.addLocal('certs', certPath(settingsRef.current.device, full.t), full);
      setCertRecords((xs) => [...xs, full]);
      requestSync(0);
    },
    [requestSync],
  );

  const finishSession = useCallback(
    async (score: number, answered: number) => {
    const s = session;
    setSession(null);
    if (s && answered > 0) {
      const rec: SessionRecord = { t: isoNow(), mode: s.mode, score, n: answered };
      await DB.addLocal('sessions', sessionPath(settingsRef.current.device, rec.t), rec);
      setSessions((xs) => [...xs, rec]);
    }
    requestSync(0);
    const a = await DB.allAttempts();
    await remind(catalogRef.current, a);
    },
    [session, requestSync, remind],
  );

  // read on each render, so a raise ends at the rollover without a timer
  const newLimit = todayLimit(settingRecords, raises, Date.now());
  const raiseNew = useCallback(async () => {
    const rec: RaiseRecord = { t: isoNow(), n: NEW_STEP };
    await DB.addLocal('raises', raisePath(settingsRef.current.device, rec.t), rec);
    setRaises((xs) => [...xs, rec]);
    requestSync(0);
  }, [requestSync]);
  const setSetting = useCallback(
    async (name: SettingName, n: number) => {
      const rec: SettingRecord = { t: isoNow(), name, n };
      await DB.addLocal('setting_changes', settingPath(settingsRef.current.device, rec.t), rec);
      setSettingRecords((xs) => [...xs, rec]);
      requestSync(0);
    },
    [requestSync],
  );
  const courseOrder = useMemo(() => moduleOrder(orders), [orders]);
  const setCourseOrder = useCallback(
    async (courses: string[]) => {
      const rec: OrderRecord = { t: isoNow(), courses };
      await DB.addLocal('orders', orderPath(settingsRef.current.device, rec.t), rec);
      setOrders((xs) => [...xs, rec]);
      requestSync(0);
    },
    [requestSync],
  );

  const value = useMemo<Store>(
    () => ({
      ready,
      catalog,
      attempts,
      sessions,
      settings,
      newPerDay: newPerDay(settingRecords),
      examSize: setting(settingRecords, 'exam_size'),
      setSetting,
      newLimit,
      raiseNew,
      courseOrder,
      setCourseOrder,
      hasToken,
      sync,
      board,
      requestSync,
      updateSettings,
      signedIn,
      signOut,
      record,
      session,
      setSession,
      finishSession,
      setCourseStatus,
      focus,
      setFocus,
      setLessonState,
      archived,
      recordCertExam,
    }),
    [ready, catalog, attempts, sessions, settings, settingRecords, setSetting, newLimit, raiseNew, courseOrder, setCourseOrder, hasToken, sync, board, requestSync,
      updateSettings, signedIn, signOut, record, session, finishSession, setCourseStatus, focus, setFocus, setLessonState, archived, recordCertExam],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

/** Writes the settings and the module order an earlier build kept on the device as records, once. */
async function movedSettings(s: Settings): Promise<void> {
  const { newPerDay: kept, examSize: size, courseOrder: order } = await legacySettings();
  if (kept === undefined && size === undefined && order === undefined) return;
  const held = await DB.allSettings();
  const moved: [SettingName, number | undefined][] = [['new_per_day', kept], ['exam_size', size]];
  for (const [name, n] of moved) {
    if (typeof n !== 'number' || n === SETTING_DEFAULT[name] || held.some((r) => r.name === name)) continue;
    const rec: SettingRecord = { t: isoNow(), name, n };
    await DB.addLocal('setting_changes', settingPath(s.device, rec.t), rec);
  }
  if (order?.length && !(await DB.allOrders()).length) {
    const rec: OrderRecord = { t: isoNow(), courses: order };
    await DB.addLocal('orders', orderPath(s.device, rec.t), rec);
  }
  await saveSettings(s);
}

/** Keys this device's copy to `user`. A copy that had no owner yet is theirs: their token wrote it. */
async function own(user: string, ref: { current: string | null }): Promise<void> {
  if (!(await DB.getMeta('user'))) await DB.adopt(user);
  await DB.setMeta('user', user);
  ref.current = user;
  DB.setOwner(user);
}
