import { EditorState } from '@codemirror/state';
import { describe, expect, it } from 'vitest';

import { type EditorKey, keyed } from './keys';
import { pythonEditing } from './setup';

const editing = (doc = '', at = doc.length) =>
  EditorState.create({ doc, selection: { anchor: at }, extensions: pythonEditing() });

function typed(state: EditorState, keys: EditorKey[]): EditorState {
  for (const key of keys) state = keyed(state, key)?.state ?? state;
  return state;
}

const text = (s: string): EditorKey[] => [...s].map((one) => (one === '\n' ? 'enter' : { insert: one }));

describe('a key from the app keyboard', () => {
  it('indents after a colon and moves `else:` back to its `if`', () => {
    const state = typed(editing(), text('if a:\nb = 1\nelse:'));
    expect(state.doc.toString()).toBe('if a:\n    b = 1\nelse:');
  });

  it('removes a whole indent step with back in leading whitespace', () => {
    const state = typed(editing('def f():\n        '), ['back']);
    expect(state.doc.toString()).toBe('def f():\n    ');
  });

  it('moves the caret one character, held at either end', () => {
    expect(typed(editing('ab', 0), ['left']).selection.main.head).toBe(0);
    expect(typed(editing('ab', 2), ['right']).selection.main.head).toBe(2);
    expect(typed(editing('ab', 1), ['left']).selection.main.head).toBe(0);
  });

  it('replaces a selection with the insert', () => {
    const state = EditorState.create({ doc: 'abcd', selection: { anchor: 1, head: 3 }, extensions: pythonEditing() });
    expect(typed(state, [{ insert: 'x' }]).doc.toString()).toBe('axd');
  });

  it('indents and dedents the line by one step, wherever the caret sits', () => {
    expect(typed(editing('x = 1', 2), ['indent']).doc.toString()).toBe('    x = 1');
    expect(typed(editing('        x = 1', 10), ['dedent']).doc.toString()).toBe('    x = 1');
  });

  it('moves a line up or down at the same column, held to the line end', () => {
    const state = editing('abcdef\nab\nabcdef', 5);
    expect(typed(state, ['down']).selection.main.head).toBe(9);
    expect(typed(state, ['up']).selection.main.head).toBe(5);
    expect(typed(editing('abc\nabcdef', 9), ['up']).selection.main.head).toBe(3);
  });

  it('moves a line and duplicates one', () => {
    expect(typed(editing('a\nb\nc', 2), ['lineUp']).doc.toString()).toBe('b\na\nc');
    expect(typed(editing('a\nb\nc', 2), ['lineDown']).doc.toString()).toBe('a\nc\nb');
    expect(typed(editing('a\nb', 2), ['duplicate']).doc.toString()).toBe('a\nb\nb');
  });

  it('selects the block around the caret by indentation, wider on each press', () => {
    const doc = 'def f(a):\n    if a:\n        b = 1\n        c = 2\n    return a';
    let state = editing(doc, doc.indexOf('b = 1') + 2);
    const picked = () => state.sliceDoc(state.selection.main.from, state.selection.main.to);
    state = typed(state, ['block']);
    expect(picked()).toBe('        b = 1\n        c = 2');
    state = typed(state, ['block']);
    expect(picked()).toBe('    if a:\n        b = 1\n        c = 2');
    state = typed(state, ['block']);
    expect(picked()).toBe('    if a:\n        b = 1\n        c = 2\n    return a');
    state = typed(state, ['block']);
    expect(picked()).toBe(doc);
  });

  it('indents a selected block whole, and nothing beside it', () => {
    const doc = 'def f(a):\n    if a:\n        b = 1\n        c = 2\n    return a';
    const state = typed(editing(doc, doc.indexOf('b = 1')), ['block', 'indent']);
    expect(state.doc.toString()).toBe('def f(a):\n    if a:\n            b = 1\n            c = 2\n    return a');
  });

  it('pairs a bracket as it is typed, steps over the closing one, and deletes an empty pair', () => {
    expect(typed(editing(), text('f(')).doc.toString()).toBe('f()');
    const stepped = typed(editing(), text('f(x)'));
    expect(stepped.doc.toString()).toBe('f(x)');
    expect(stepped.selection.main.head).toBe(4);
    expect(typed(editing(), [...text('['), 'back']).doc.toString()).toBe('');
    expect(typed(editing(), text("'a")).doc.toString()).toBe("'a'");
  });

  it('puts a name in place of the part of it typed before the caret', () => {
    const state = typed(editing('total = 0\nx = to'), [{ name: 'total' }]);
    expect(state.doc.toString()).toBe('total = 0\nx = total');
    expect(state.selection.main.head).toBe(state.doc.length);
    expect(typed(editing('x = '), [{ name: 'nums' }]).doc.toString()).toBe('x = nums');
  });
});
