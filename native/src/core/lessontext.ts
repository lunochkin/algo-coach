import type { Lesson } from './graph';

/** GitHub-style heading anchor: lowercase, punctuation dropped, spaces to hyphens (as the CLI). */
export function anchor(heading: string): string {
  return heading
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\p{M}_\- ]/gu, '')
    .replace(/ /g, '-');
}

const HEADING = /^#{2,3}\s+(.+?)\s*#*\s*$/;

/** `##` and `###` headings outside code fences: anchor -> heading text. */
export function headings(md: string): Record<string, string> {
  const out: Record<string, string> = {};
  let fenced = false;
  for (const line of md.split(/\r\n|\r|\n/)) {
    if (line.trimStart().startsWith('```')) fenced = !fenced;
    else if (!fenced) {
      const m = HEADING.exec(line);
      if (m && !(anchor(m[1]) in out)) out[anchor(m[1])] = m[1];
    }
  }
  return out;
}

export function minutesOf(x: Pick<Lesson, 'minutes'>, body: string): number {
  return x.minutes ?? Math.max(1, Math.ceil(body.split(/\s+/).filter(Boolean).length / 200));
}

/** In-lesson links: [text](lesson:slug) and [text](lesson:slug#anchor). */
export function lessonLinks(body: string): [slug: string, anchor: string][] {
  return [...body.matchAll(/\]\(lesson:([^)#\s]+)(?:#([^)\s]+))?\)/g)].map((m) => [m[1], m[2] ?? '']);
}

/** Why "slug" or "slug#anchor" does not resolve, or null (same wording as the CLI). */
export function lessonRefError(ref: string, bodies: Record<string, string>): string | null {
  const at = ref.indexOf('#');
  const slug = at < 0 ? ref : ref.slice(0, at);
  const frag = at < 0 ? '' : ref.slice(at + 1);
  if (!(slug in bodies)) return `unknown lesson '${slug}'`;
  if (frag && !(frag in headings(bodies[slug]))) return `no section #${frag} in lesson ${slug}`;
  return null;
}

/** A lesson cut at its `##`/`###` headings (outside code fences), so the reader can scroll to one. */
export function sections(md: string): { anchor: string | null; text: string }[] {
  const out: { anchor: string | null; text: string[] }[] = [{ anchor: null, text: [] }];
  let fenced = false;
  for (const line of md.split(/\r\n|\r|\n/)) {
    if (line.trimStart().startsWith('```')) fenced = !fenced;
    const m = !fenced ? HEADING.exec(line) : null;
    if (m) out.push({ anchor: anchor(m[1]), text: [] });
    out[out.length - 1].text.push(line);
  }
  return out.map((s) => ({ anchor: s.anchor, text: s.text.join('\n') })).filter((s) => s.text.trim());
}
