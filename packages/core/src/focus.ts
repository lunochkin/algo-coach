import { certScope, COURSE_SCOPE, LEVEL_SLUGS } from './certs';
import { cmp, subTitle, topicTitle, type Catalog } from './courses';
import type { Question } from './types';

/** What `next` serves when set: a course, optionally narrowed to a topic and sub. */
export interface Focus {
  course: string;
  topic: string | null;
  sub: string | null;
  strict?: boolean; // reviews from the focus only; default relaxed: reviews from everywhere
  cert?: string | null; // a certificate focus: `scope` replaces topic/sub matching
  scope?: Set<string>; // "sub@level" groups of the certificate and its prerequisites
}

export interface FocusRecord {
  t: string;
  course: string | null; // null: cleared
  topic: string | null;
  sub: string | null;
  strict?: boolean; // absent in older records: relaxed
  cert?: string | null; // absent: not a certificate focus
}

/** Newest record (stable by `t`, file order breaks ties), degraded to what still exists. */
export function currentFocus(records: FocusRecord[], cat: Catalog): Focus | null {
  const last = [...records].sort((a, b) => cmp(a.t, b.t)).at(-1);
  if (!last?.course) return null;
  const c = cat.courses.find((x) => x.slug === last.course);
  if (!c) return null;
  const strict = !!last.strict;
  const x = last.cert ? c.certs?.get(last.cert) : undefined;
  if (x) {
    const topic = x.scope === COURSE_SCOPE ? null : x.scope;
    return { course: c.slug, topic, sub: null, strict, cert: x.id, scope: certScope(c, x) };
  }
  const t = c.topics.find((x) => x.slug === last.topic);
  if (!t) return { course: c.slug, topic: null, sub: null, strict };
  const sub = last.sub && t.subs.includes(last.sub) ? last.sub : null;
  return { course: c.slug, topic: t.slug, sub, strict };
}

/** Same course, topic and sub (strictness aside). */
export function sameFocus(a: Focus | null, b: Focus | null): boolean {
  return (
    (a?.course ?? null) === (b?.course ?? null) &&
    a?.topic === b?.topic &&
    a?.sub === b?.sub &&
    (a?.cert ?? null) === (b?.cert ?? null)
  );
}

export function inFocus(q: Question, f: Focus): boolean {
  if (f.scope) return q.course === f.course && f.scope.has(`${q.sub}@${q.level}`);
  return (
    q.course === f.course &&
    (f.topic === null || q.topic === f.topic) &&
    (f.sub === null || q.sub === f.sub)
  );
}

/** "Python › concurrency › asyncio-core", or "all courses". */
export function focusLabel(f: Focus | null, cat: Catalog | null): string {
  if (!f) return 'all courses';
  const c = cat?.courses.find((x) => x.slug === f.course);
  const title = c?.title ?? f.course;
  if (f.cert) return `${title} › ${c?.certs?.get(f.cert)?.title ?? f.cert}`;
  // titles, not slugs: two topics can each hold a subtopic called basics
  return [title, f.topic && topicTitle(c, f.topic), f.sub && subTitle(c, f.sub)].filter(Boolean).join(' › ');
}

/** Where a level exam opens: the focus's module, and a certification focus's level; Associate where none names one. */
export function examOpening(f: Focus | null): { course: string | null; level: number } {
  const named = f?.cert ? LEVEL_SLUGS.indexOf(f.cert.slice(f.cert.lastIndexOf('-') + 1)) : -1;
  return { course: f?.course ?? null, level: named >= 0 ? named : 1 };
}
