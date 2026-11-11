import { describe, expect, it } from 'vitest';

import { sectionOpened, sectionToggled } from './index';

describe("a long page's sections", () => {
  it("closes a section on its heading's press, and opens it on the next", () => {
    expect(sectionToggled([], 'a')).toEqual(['a']);
    expect(sectionToggled(['a', 'b'], 'a')).toEqual(['b']);
  });

  it('opens the section a jump lands on, and leaves the rest', () => {
    expect(sectionOpened(['a', 'b'], 'a')).toEqual(['b']);
    expect(sectionOpened(['b'], 'a')).toEqual(['b']);
  });
});
