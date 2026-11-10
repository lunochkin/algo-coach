import type { RawQuestion } from './types';

const FIELDS = ['mechanism', 'example', 'pitfalls', 'versions', 'diagram'];

const nonEmpty = (x: unknown) => typeof x === 'string' && x.trim() !== '';
const strings = (v: unknown, lo: number, hi: number) =>
  Array.isArray(v) && v.length >= lo && v.length <= hi && v.every(nonEmpty);

/** Mirror of the CLI's check_detail, same wording, so the shared fixtures cover both. */
export function checkDetail(raw: RawQuestion & Record<string, unknown>): string[] {
  const errors: string[] = [];
  const d = raw.detail as unknown;
  if (typeof d === 'string') errors.push('detail must be a table with mechanism (a plain string is legacy)');
  else if (d && typeof d === 'object') {
    const t = d as Record<string, unknown>;
    if (!nonEmpty(t.mechanism)) errors.push('detail.mechanism is required');
    for (const f of ['example', 'versions', 'diagram'])
      if (f in t && !nonEmpty(t[f])) errors.push(`detail.${f} must be a non-empty string`);
    if ('pitfalls' in t && !strings(t.pitfalls, 1, 4)) errors.push('detail.pitfalls must be 1-4 non-empty strings');
    const extra = Object.keys(t)
      .filter((k) => !FIELDS.includes(k))
      .sort();
    if (extra.length) errors.push(`detail has unknown fields [${extra.map((k) => `'${k}'`).join(', ')}]`);
  } else if (d !== undefined && d !== null) errors.push('detail must be a table');
  for (const [name, parent] of [
    ['key_detail', 'key'],
    ['traps_detail', 'traps'],
  ] as const) {
    if (!(name in raw)) continue;
    const v = raw[name];
    const p = raw[parent];
    const n = Array.isArray(p) ? p.length : 0;
    if (!strings(v, n, n)) errors.push(`${name} must have one non-empty string per ${parent} item (${n})`);
    else if ((v as string[]).some((x) => x.trim().split(/\r\n|\r|\n/).length > 3))
      errors.push(`${name} items must be at most 3 lines`);
  }
  return errors;
}
