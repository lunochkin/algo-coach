import { deleteCharBackward, insertNewlineAndIndent } from '@codemirror/commands';
import { ensureSyntaxTree } from '@codemirror/language';
import { EditorSelection, type EditorState, type StateCommand, type Transaction } from '@codemirror/state';

// a key a keyboard drawn by the app sends, rather than one the system's
// keyboard types into the page
export type EditorKey = { insert: string } | 'back' | 'left' | 'right' | 'enter';

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
