import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { Board, certConditions, certFocus, certStates, loadSnapshot, readyCert, type Snapshot } from './index';

// the shared fixtures, which the Python side generates: `README.md`, Boundaries
const fixtures = JSON.parse(readFileSync(resolve(__dirname, '../../../tests/fixtures/knowledge/scheduling.json'), 'utf8'));
const named = (name: string) => {
  const f = fixtures.cert_states.find((x: { name: string }) => x.name === name);
  const cat = loadSnapshot({ format: 6, courses: f.courses } as Snapshot);
  return { cat, c: cat.courses[0], b: Board.build(cat, f.records), exams: f.exams ?? [] };
};

describe("a certification's conditions", () => {
  it('offers its exam once every other condition holds', () => {
    const { c, b, exams } = named('covered and retained: ready');
    const states = certStates(b, c, exams);
    const [id] = [...states].find(([, s]) => s.state === 'ready')!;
    const v = certConditions(b, c, id, states, null)!;
    expect([v.label, v.offersExam, v.offersTarget]).toEqual(['Ready for exam', true, true]);
    expect(v.checks.filter((x) => x.text.startsWith('Coverage') || x.text.startsWith('Retention')).every((x) => x.ok)).toBe(true);
  });

  it('names the groups still below coverage, before the exam is offered', () => {
    const { c, b, exams } = named('nothing done');
    const states = certStates(b, c, exams);
    const [id] = [...states].find(([, s]) => s.state === 'in_progress' || s.state === 'locked')!;
    const v = certConditions(b, c, id, states, null)!;
    expect(v.offersExam).toBe(false);
    expect(v.short.length).toBeGreaterThan(0);
  });

  it('marks the certification the focus aims at', () => {
    const { c, b, exams } = named('nothing done');
    const states = certStates(b, c, exams);
    const [id] = [...states][0];
    const focus = certFocus(c, id, false);
    expect(certConditions(b, c, id, states, focus)!.targeted).toBe(true);
  });
});

describe('the home', () => {
  it('names the first certification ready for its exam', () => {
    const { b, exams } = named('covered and retained: ready');
    expect(readyCert(b, [], exams)?.line).toMatch(/^Ready for exam: /);
  });

  it('names none where nothing is ready', () => {
    const { b, exams } = named('nothing done');
    expect(readyCert(b, [], exams)).toBeNull();
  });
});
