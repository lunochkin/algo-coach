import { describe, expect, it } from 'vitest';

import { examOpening } from './focus';

describe('the exam opening', () => {
  it('opens on Associate across every module without a focus', () => {
    expect(examOpening(null)).toEqual({ course: null, level: 1 });
  });

  it("opens on the focus's module", () => {
    expect(examOpening({ course: 'python', topic: 'core', sub: null })).toEqual({ course: 'python', level: 1 });
  });

  it("takes a certification focus's level", () => {
    const f = { course: 'python', topic: 'core', sub: null, cert: 'python-core-professional' };
    expect(examOpening(f)).toEqual({ course: 'python', level: 2 });
  });
});
