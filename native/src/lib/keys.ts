// the app's own keyboard: what a key press does to the text and the caret.
// The system keyboard hides the symbols code and a `short` reply are made of,
// and its suggestion strip completes words

export interface Selection {
  start: number;
  end: number;
}

export interface Edit {
  text: string;
  selection: Selection;
}

export type Key = { insert: string } | 'back' | 'left' | 'right';

export const EMPTY: Edit = { text: '', selection: { start: 0, end: 0 } };

const at = (text: string, caret: number): Edit => ({ text, selection: { start: caret, end: caret } });

/** The text and caret after one press. A selection is replaced by an insert and removed by back. */
export function pressed(edit: Edit, key: Key): Edit {
  const { text } = edit;
  const start = Math.min(edit.selection.start, edit.selection.end);
  const end = Math.max(edit.selection.start, edit.selection.end);
  if (key === 'left') return at(text, start === end ? Math.max(0, start - 1) : start);
  if (key === 'right') return at(text, start === end ? Math.min(text.length, end + 1) : end);
  if (key === 'back') {
    if (start !== end) return at(text.slice(0, start) + text.slice(end), start);
    if (start === 0) return edit;
    return at(text.slice(0, start - 1) + text.slice(start), start - 1);
  }
  return at(text.slice(0, start) + key.insert + text.slice(end), start + key.insert.length);
}

// shift capitalises the next letter, and a second tap close after the first
// holds it. It changes the letters alone, so every symbol stays one tap
export type Shift = 'off' | 'once' | 'lock';

export const DOUBLE_TAP_MS = 300;

export function shiftPressed(shift: Shift, sinceLastMs: number): Shift {
  if (shift === 'once' && sinceLastMs < DOUBLE_TAP_MS) return 'lock';
  return shift === 'off' ? 'once' : 'off';
}

export const afterLetter = (shift: Shift): Shift => (shift === 'once' ? 'off' : shift);

export const cased = (letter: string, shift: Shift) => (shift === 'off' ? letter : letter.toUpperCase());

// two rows of the symbols Python is written with, above the digits and the
// letters, so a reply or a line of code needs no layer
export const SYMBOLS: string[][] = [
  ['(', ')', '[', ']', '{', '}', '<', '>', '=', ':'],
  ['+', '-', '*', '/', '%', '!', '&', '|', "'", '"'],
];

export const DIGITS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];

// `_` and `.` sit among the letters, since names and attributes use them
export const LETTERS: string[][] = [
  ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
  ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '_'],
  ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.'],
];

// the rare symbols, and the values a `short` reply most often is, on a layer
// that takes the letters' place
export const RARE = ['#', '@', '\\', '^', '~', ';', '$', '`'];
export const WORDS = ['True', 'False', 'None'];
