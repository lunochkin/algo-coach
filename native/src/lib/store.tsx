import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AppState } from 'react-native';

import {
  attemptPath,
  Board,
  isoNow,
  sessionPath,
  statusPath,
  currentFocus,
  focusPath,
  type Focus,
  type FocusRecord,
  type LessonRecord,
  lessonPath,
  withLessons,
  withCertExams,
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
  raised,
  todayLimit,
  type Raise,
} from '@/core';

import { readCatalog } from './courses-cache';
import * as DB from './db';
import { scheduleReminder } from './notify';
import { DEFAULTS, getToken, loadSettings, saveSettings, setToken, type Settings } from './settings';
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
  // today's new-question limit: the setting plus today's raise, until the 04:00 rollover
  newLimit: number;
  raiseNew: () => Promise<void>;
  hasToken: boolean;
  sync: SyncState;
  filter: string | null;
  setFilter: (slug: string | null) => void;
  board: (only?: string | null, include?: string | null) => Board | null;
  requestSync: (delayMs?: number) => void;
  updateSettings: (s: Settings) => Promise<void>;
  updateToken: (token: string) => Promise<void>;
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
  const full = useMemo(
    // Lesson progress is learner state too: newest record per lesson across devices.
    () =>
      rawCatalog
        ? withCertExams(withLessons(withStatuses(rawCatalog, statuses), lessonRecords), certRecords)
        : null,
    [rawCatalog, statuses, lessonRecords, certRecords],
  );
  // Archived courses are hidden everywhere except Settings, where they can be restored.
  const archived = useMemo(() => full?.courses.filter((c) => c.archived) ?? [], [full]);
  const catalog = useMemo(() => (full ? visibleCatalog(full) : null), [full]);
  const focus = useMemo(
    () => (catalog ? currentFocus(focusRecords, catalog) : null),
    [catalog, focusRecords],
  );
  const [attempts, setAttempts] = useState<AttemptRecord[]>([]);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [settings, setSettings] = useState<Settings>(DEFAULTS);
  const [raise, setRaise] = useState<Raise | null>(null);
  const [hasToken, setHasToken] = useState(false);
  const [sync, setSync] = useState<SyncState>({ running: false, lastAt: null, error: null });
  const [filter, setFilter] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);

  const settingsRef = useRef(settings);
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
      const r = await syncOnce(settingsRef.current, token);
      const lastAt = new Date().toISOString();
      await DB.setMeta('last_sync', lastAt);
      await DB.setMeta('last_error', '');
      const { a, cat } = await reload(r.coursesChanged);
      setSync({ running: false, lastAt, error: null });
      await remind(cat ?? catalogRef.current, a);
    } catch (e) {
      failed = true;
      const error = e instanceof Error ? e.message : String(e);
      await DB.setMeta('last_error', error);
      setSync((x) => ({ ...x, running: false, error }));
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
      const s = await loadSettings();
      setSettings(s);
      settingsRef.current = s;
      const kept = await DB.getMeta('new_raise');
      setRaise(kept ? (JSON.parse(kept) as Raise) : null);
      setHasToken(!!(await getToken()));
      const lastAt = await DB.getMeta('last_sync');
      const error = (await DB.getMeta('last_error')) || null;
      setSync({ running: false, lastAt, error });
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

  const updateToken = useCallback(async (token: string) => {
    await setToken(token);
    setHasToken(!!token);
  }, []);

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
      const rec: FocusRecord = {
        t: isoNow(),
        course: f?.course ?? null,
        topic: f?.topic ?? null,
        sub: f?.sub ?? null,
        strict: !!f?.strict,
        ...(f?.cert ? { cert: f.cert } : {}),
      };
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
  const newLimit = todayLimit(settings.newPerDay, raise, Date.now());
  const raiseNew = useCallback(async () => {
    const next = raised(raise, Date.now());
    await DB.setMeta('new_raise', JSON.stringify(next));
    setRaise(next);
  }, [raise]);

  const value = useMemo<Store>(
    () => ({
      ready,
      catalog,
      attempts,
      sessions,
      settings,
      newLimit,
      raiseNew,
      hasToken,
      sync,
      filter,
      setFilter,
      board,
      requestSync,
      updateSettings,
      updateToken,
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
    [ready, catalog, attempts, sessions, settings, newLimit, raiseNew, hasToken, sync, filter, board, requestSync,
      updateSettings, updateToken, record, session, finishSession, setCourseStatus, focus, setFocus, setLessonState, archived, recordCertExam],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
