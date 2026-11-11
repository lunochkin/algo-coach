import { closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete';
import { history } from '@codemirror/commands';
import { python } from '@codemirror/lang-python';
import { bracketMatching, indentOnInput, indentUnit, syntaxHighlighting } from '@codemirror/language';
import { EditorState, type Extension } from '@codemirror/state';
import { highlightActiveLine, highlightActiveLineGutter, keymap, lineNumbers } from '@codemirror/view';

import { HIGHLIGHTER } from './python';

/**
 * How Python is edited on every client: highlighting, indentation and paired
 * brackets, and no `autocompletion()`. `flows.md` gives why the editor
 * proposes no library name, and a closing bracket names none. A client adds its
 * own keymap and its own look.
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
    closeBrackets(),
    // backspace in an empty pair takes both halves
    keymap.of(closeBracketsKeymap),
    syntaxHighlighting(HIGHLIGHTER),
    python(),
  ];
}
