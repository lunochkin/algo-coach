import { describe, expect, it } from 'vitest';

import { afterLetter, cased, DOUBLE_TAP_MS, EMPTY, type Edit, type Key, pressed, shiftPressed } from './keys';

const typed = (keys: Key[], from: Edit = EMPTY) => keys.reduce(pressed, from);
const caret = (text: string, at: number): Edit => ({ text, selection: { start: at, end: at } });

describe("the app's keyboard", () => {
  it('inserts at the caret and moves it past the insert', () => {
    expect(typed([{ insert: '[' }, { insert: '1' }, { insert: ']' }])).toEqual(caret('[1]', 3));
    expect(pressed(caret('[]', 1), { insert: 'None' })).toEqual(caret('[None]', 5));
  });

  it('replaces a selection with the insert', () => {
    expect(pressed({ text: 'a, b', selection: { start: 3, end: 0 } }, { insert: 'x' })).toEqual(caret('xb', 1));
  });

  it('deletes the character before the caret, or the selection', () => {
    expect(pressed(caret('[1, 2]', 5), 'back')).toEqual(caret('[1, ]', 4));
    expect(pressed({ text: '[1, 2]', selection: { start: 1, end: 5 } }, 'back')).toEqual(caret('[]', 1));
    expect(pressed(caret('[]', 0), 'back')).toEqual(caret('[]', 0));
  });

  it('moves the caret one character, held at either end', () => {
    expect(pressed(caret('ab', 0), 'left')).toEqual(caret('ab', 0));
    expect(pressed(caret('ab', 2), 'right')).toEqual(caret('ab', 2));
    expect(pressed(caret('ab', 1), 'right')).toEqual(caret('ab', 2));
  });

  it('collapses a selection to the side the arrow points at', () => {
    const selected: Edit = { text: 'abcd', selection: { start: 1, end: 3 } };
    expect(pressed(selected, 'left')).toEqual(caret('abcd', 1));
    expect(pressed(selected, 'right')).toEqual(caret('abcd', 3));
  });
});

describe('shift', () => {
  it('capitalises the next letter alone', () => {
    const shift = shiftPressed('off', 5000);
    expect(shift).toBe('once');
    expect(cased('q', shift)).toBe('Q');
    expect(afterLetter(shift)).toBe('off');
  });

  it('holds on a second tap close after the first, and a third releases it', () => {
    const held = shiftPressed('once', DOUBLE_TAP_MS - 1);
    expect(held).toBe('lock');
    expect(afterLetter(held)).toBe('lock');
    expect(shiftPressed(held, 5000)).toBe('off');
  });

  it('releases on a second tap that comes late', () => {
    expect(shiftPressed('once', DOUBLE_TAP_MS)).toBe('off');
  });
});
