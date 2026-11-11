import { wordBefore } from './names';
import { deleteBracketPair, insertBracket } from '@codemirror/autocomplete';
import {
  copyLineDown,
  deleteCharBackward,
  indentLess,
  indentMore,
  insertNewlineAndIndent,
  moveLineDown,
  moveLineUp,
} from '@codemirror/commands';
import { ensureSyntaxTree } from '@codemirror/language';
import { EditorSelection, type EditorState, type StateCommand, type Transaction } from '@codemirror/state';

// a key a keyboard drawn by the app sends, rather than one the system's
// keyboard types into the page. The line keys move or duplicate a line, and
// select the block around the caret, wider on each press, for indent and
// dedent to move whole
export type EditorKey =
  | { insert: string }
  // a declared name, in place of the part of it typed before the caret
  | { name: string }
  | 'back'
  | 'left'
  | 'right'
  | 'up'
  | 'down'
  | 'enter'
  | 'indent'
  | 'dedent'
  | 'lineUp'
  | 'lineDown'
  | 'duplicate'
  | 'block';

// the reindent reads the syntax tree, which the parser otherwise fills in
// idle time: a key arriving before it would indent against a stale tree
const PARSE_MS = 20;

/** The transaction one key makes, or none where it changes nothing. */
export function keyed(state: EditorState, key: EditorKey): Transaction | null {
  ensureSyntaxTree(state, state.doc.length, PARSE_MS);
  let made: Transaction | null = null;
  const run = (command: StateCommand) => command({ state, dispatch: (tr) => (made = tr) });
  if (key === 'enter') run(insertNewlineAndIndent);
  // typed as a view command, and reads no more than the state where no view is given
  // a pair typed empty goes as one, as the system keyboard's backspace takes it
  else if (key === 'back') run(deleteBracketPair) || run(deleteCharBackward as unknown as StateCommand);
  else if (key === 'indent') run(indentMore);
  else if (key === 'dedent') run(indentLess);
  else if (key === 'lineUp') run(moveLineUp);
  else if (key === 'lineDown') run(moveLineDown);
  else if (key === 'duplicate') run(copyLineDown);
  else if (key === 'block') made = state.update({ selection: blockAround(state), scrollIntoView: true });
  else if (key === 'up' || key === 'down') made = lineMove(state, key === 'up' ? -1 : 1);
  else if (key === 'left' || key === 'right') {
    const step = key === 'left' ? -1 : 1;
    made = state.update({
      selection: EditorSelection.create(
        state.selection.ranges.map((range) =>
          range.empty
            ? EditorSelection.cursor(Math.min(state.doc.length, Math.max(0, range.head + step)))
            : EditorSelection.cursor(step < 0 ? range.from : range.to),
        ),
      ),
      scrollIntoView: true,
    });
  } else if ('name' in key) {
    const head = state.selection.main.head;
    const typed = wordBefore(state.doc.lineAt(head).text.slice(0, head - state.doc.lineAt(head).from));
    made = state.update({
      changes: { from: head - typed.length, to: head, insert: key.name },
      selection: { anchor: head - typed.length + key.name.length },
      userEvent: 'input.type',
      scrollIntoView: true,
    });
  }
  // a bracket or a quote pairs as the page's own typing pairs it, since the
  // pairing reads the page's input and the app's keys never reach it
  else if (key.insert.length === 1 && (made = insertBracket(state, key.insert))) return made;
  // marked as typed, or `indentOnInput` leaves `else:` where it was typed
  else made = state.update({ ...state.replaceSelection(key.insert), userEvent: 'input.type', scrollIntoView: true });
  return made;
}

// a line of the document up or down, at the same column, held to the line's
// end. A wrapped line is one line here, as it is to the file
function lineMove(state: EditorState, step: number): Transaction {
  return state.update({
    selection: EditorSelection.create(
      state.selection.ranges.map((range) => {
        const line = state.doc.lineAt(range.head);
        const target = line.number + step;
        if (target < 1 || target > state.doc.lines) return EditorSelection.cursor(range.head);
        const to = state.doc.line(target);
        return EditorSelection.cursor(Math.min(to.to, to.from + (range.head - line.from)));
      }),
    ),
    scrollIntoView: true,
  });
}

const indentOf = (text: string) => /^\s*/.exec(text)![0].length;
const blank = (text: string) => text.trim() === '';

/**
 * The block around the selection, by indentation as Python reads it: the run
 * of lines at least as deep as the caret's line, then on each press the
 * header above it, then the header's siblings, and so on outward. Always whole lines, so indent and
 * dedent move the block and nothing beside it.
 */
function blockAround(state: EditorState): EditorSelection {
  const { doc } = state;
  const range = state.selection.main;
  const first = doc.lineAt(range.from).number;
  const last = doc.lineAt(range.to).number;
  const whole = (a: number, b: number) => EditorSelection.single(doc.line(a).from, doc.line(b).to);

  // the run of lines around [a, b] no shallower than `depth`, blank ones within it
  const run = (a: number, b: number, depth: number): [number, number] => {
    while (a > 1 && (blank(doc.line(a - 1).text) || indentOf(doc.line(a - 1).text) >= depth)) a--;
    while (b < doc.lines && (blank(doc.line(b + 1).text) || indentOf(doc.line(b + 1).text) >= depth)) b++;
    while (a < b && blank(doc.line(a).text)) a++;
    while (b > a && blank(doc.line(b).text)) b--;
    return [a, b];
  };

  const depth = Math.min(
    ...Array.from({ length: last - first + 1 }, (_, i) => doc.line(first + i).text)
      .filter((text) => !blank(text))
      .map(indentOf),
  );
  const [a, b] = run(first, last, Number.isFinite(depth) ? depth : 0);
  const selected = range.from === doc.line(a).from && range.to === doc.line(b).to;
  if (!selected) return whole(a, b);
  // the whole run is selected already: add the header above it. The press
  // after reaches the header's siblings, since the header is shallower
  return whole(a > 1 ? a - 1 : a, b);
}
