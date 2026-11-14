import type { EditorKey } from '@climb/editor';

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

// one key type for a one-line field and the editor alike
export type Key = EditorKey;

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
  if (typeof key === 'string' || !('insert' in key)) return edit;
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
// where the bottom row holds enter, `?` joins them
export const RARE_LINES = [...RARE, '?'];
export const WORDS = ['True', 'False', 'None'];

// Python's keywords, a key each, in the order a solution reaches for them.
// Keywords alone: a name from the language's library, or a line of a form,
// would be a hint, and the recall measures exactly that
export const KEYWORDS: string[][] = [
  ['def', 'return', 'if', 'elif', 'else', 'for', 'while', 'in'],
  ['not', 'and', 'or', 'is', 'None', 'True', 'False', 'pass'],
  ['break', 'continue', 'lambda', 'yield', 'class', 'import', 'from', 'with'],
];

// a keyword something always follows takes its space with it
const BARE = new Set(['else', 'pass', 'break', 'continue', 'None', 'True', 'False']);
export const keywordText = (word: string) => (BARE.has(word) ? word : `${word} `);
