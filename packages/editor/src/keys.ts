import { deleteCharBackward, indentLess, indentMore, insertNewlineAndIndent } from '@codemirror/commands';
import { ensureSyntaxTree } from '@codemirror/language';
import { EditorSelection, type EditorState, type StateCommand, type Transaction } from '@codemirror/state';

// a key a keyboard drawn by the app sends, rather than one the system's
// keyboard types into the page
export type EditorKey = { insert: string } | 'back' | 'left' | 'right' | 'up' | 'down' | 'enter' | 'indent' | 'dedent';

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
  else if (key === 'back') run(deleteCharBackward as unknown as StateCommand);
  else if (key === 'indent') run(indentMore);
  else if (key === 'dedent') run(indentLess);
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
  }
  // marked as typed, or `indentOnInput` leaves `else:` where it was typed
  else made = state.update({ ...state.replaceSelection(key.insert), userEvent: 'input.type', scrollIntoView: true });
  return made;
}

// a line up or down at the same column, held to the line's end: the phone's
// editor wraps no line, so a column is a place on the screen
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
