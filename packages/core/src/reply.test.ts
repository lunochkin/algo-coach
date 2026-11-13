import { describe, expect, it } from 'vitest';

import { spans } from './reply';

describe('spans', () => {
  it('marks the text between a backtick pair as code', () => {
    // a question's feedback renders inline code as a lesson does
    expect(spans('`0` and `[]` are false')).toEqual([
      { text: '0', code: true },
      { text: ' and ', code: false },
      { text: '[]', code: true },
      { text: ' are false', code: false },
    ]);
  });

  it('leaves a lone backtick as text', () => {
    // an unmatched mark is the author's character, not the start of code
    expect(spans('a ` b')).toEqual([{ text: 'a ` b', code: false }]);
  });

  it('keeps prose with no backtick whole', () => {
    expect(spans('plain')).toEqual([{ text: 'plain', code: false }]);
  });
});
