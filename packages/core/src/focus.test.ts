import { describe, expect, it } from 'vitest';

import { aimedAt, aimFocus } from './index';

describe('aiming the focus', () => {
  it('reads aimed only at the exact module, topic and subtopic the focus names', () => {
    const f = { course: 'm', topic: 't', sub: null };
    expect(aimedAt(f, 'm', 't', null)).toBe(true);
    expect(aimedAt(f, 'm', null, null)).toBe(false);
    expect(aimedAt(f, 'm', 't', 's')).toBe(false);
    expect(aimedAt(null, 'm', null, null)).toBe(false);
  });

  it('reads a certification focus as aimed at no group of its scope', () => {
    expect(aimedAt({ course: 'm', topic: 't', sub: null, cert: 'x' }, 'm', 't', null)).toBe(false);
  });

  it("carries the current focus's strictness over to a new aim", () => {
    const strict = { course: 'm', topic: null, sub: null, strict: true };
    expect(aimFocus(strict, { course: 'n', topic: 't', sub: null }).strict).toBe(true);
    expect(aimFocus(null, { course: 'n', topic: 't', sub: null, strict: true }).strict).toBe(false);
  });
});
