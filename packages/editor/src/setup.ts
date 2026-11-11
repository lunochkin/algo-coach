import { history } from '@codemirror/commands';
import { python } from '@codemirror/lang-python';
import { bracketMatching, indentOnInput, indentUnit, syntaxHighlighting } from '@codemirror/language';
import { EditorState, type Extension } from '@codemirror/state';
import { highlightActiveLine, highlightActiveLineGutter, lineNumbers } from '@codemirror/view';

import { HIGHLIGHTER } from './python';

/**
 * How Python is edited on every client: highlighting and indentation, and no
 * `autocompletion()`. `flows.md` gives why the editor proposes nothing. A
 * client adds its own keymap and its own look.
 */
export function pythonEditing(): Extension[] {
  return [
    lineNumbers(),
    highlightActiveLineGutter(),
    highlightActiveLine(),
    history(),
    indentOnInput(),
    indentUnit.of('    '),
    EditorState.tabSize.of(4),
    bracketMatching(),
    syntaxHighlighting(HIGHLIGHTER),
    python(),
  ];
}
