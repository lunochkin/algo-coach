import { describe, expect, it } from 'vitest';

import type { CertStatus } from '../certs';
import type { Course } from '../types';
import { certCell, moduleFailed, moduleMeta, noGraph, practiceShare, startTitle } from './module';

describe('module words', () => {
  it('counts topics in the singular for one', () => {
    expect(moduleMeta(1, 3, false)).toBe('1 topic · 3 due · active');
    expect(moduleMeta(2, 0, true)).toBe('2 topics · 0 due · paused');
  });

  it('names what failed to load the module', () => {
    expect(moduleFailed('courses.json: bad')).toBe('The module did not load: courses.json: bad');
  });

  it('names an invalid graph by its first error', () => {
    expect(noGraph({ title: 'Python', graphErrors: ['cycle'] })).toBe(
      'The prerequisite graph of Python is invalid and ignored: cycle',
    );
    expect(noGraph({ title: 'Python', graphErrors: [] })).toBe('Python has no prerequisite graph.');
  });

  it('reads a practice-only cell by its passed share', () => {
    const s = (state: CertStatus['state']) => ({ state, passed: 2, questions: 5 }) as CertStatus;
    expect(certCell('Stdlib · Associate', s('not_certified'))).toBe('Stdlib · Associate: practice only, 2 of 5 passed');
    expect(certCell('Stdlib · Associate', s('ready'))).toBe('Stdlib · Associate: Ready for exam');
    expect(practiceShare({ passed: 2, questions: 5 })).toBe('2/5');
    expect(practiceShare({ passed: 0, questions: 0 })).toBe('—');
  });

  it('titles the start sheet by its narrowest scope', () => {
    const c = { title: 'Python', topics: [{ slug: 'core', title: 'Core', subs: ['loops'], subTitles: { loops: 'Loops' } }] } as unknown as Course;
    expect(startTitle(c, { topic: null, sub: null })).toBe('Python');
    expect(startTitle(c, { topic: 'core', sub: null })).toBe('Core');
    expect(startTitle(c, { topic: 'core', sub: 'loops' })).toBe('Loops');
  });
});
