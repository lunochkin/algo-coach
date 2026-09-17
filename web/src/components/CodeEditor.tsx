import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import {
  bracketMatching,
  HighlightStyle,
  indentOnInput,
  indentUnit,
  syntaxHighlighting,
} from '@codemirror/language'
import { EditorState } from '@codemirror/state'
import {
  EditorView,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
} from '@codemirror/view'
import { tags } from '@lezer/highlight'
import { useEffect, useRef } from 'react'

// the editor reads the theme's tokens rather than CodeMirror's own colours,
// so the form is legible in whichever scheme the browser asked for
const HIGHLIGHT = HighlightStyle.define([
  { tag: [tags.keyword, tags.operatorKeyword], color: 'var(--color-code-keyword)' },
  { tag: [tags.function(tags.variableName), tags.definition(tags.variableName)], color: 'var(--color-code-name)' },
  { tag: [tags.string, tags.special(tags.string)], color: 'var(--color-code-string)' },
  { tag: [tags.number, tags.bool, tags.null], color: 'var(--color-code-number)' },
  { tag: tags.comment, color: 'var(--color-code-comment)', fontStyle: 'italic' },
])

type Props = { initial: string; onChange: (code: string) => void; onSubmit: () => void }

// highlighting and indentation, and no `autocompletion()`: `flows.md` gives
// why the editor a sitting is typed into proposes nothing
export function CodeEditor({ initial, onChange, onSubmit }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const changed = useRef(onChange)
  changed.current = onChange
  const submitted = useRef(onSubmit)
  submitted.current = onSubmit

  useEffect(() => {
    if (!host.current) return
    const view = new EditorView({
      parent: host.current,
      state: EditorState.create({
        doc: initial,
        extensions: [
          lineNumbers(),
          highlightActiveLineGutter(),
          highlightActiveLine(),
          history(),
          indentOnInput(),
          indentUnit.of('    '),
          EditorState.tabSize.of(4),
          bracketMatching(),
          syntaxHighlighting(HIGHLIGHT),
          python(),
          // ahead of the default keymap, where Mod-Enter inserts a blank line
          keymap.of([
            { key: 'Mod-Enter', run: () => (submitted.current(), true) },
            ...defaultKeymap,
            ...historyKeymap,
            indentWithTab,
          ]),
          EditorView.updateListener.of((update) => {
            if (update.docChanged) changed.current(update.state.doc.toString())
          }),
          EditorView.theme({
            '&': {
              height: '100%',
              fontSize: 'var(--text-code)',
              backgroundColor: 'var(--color-background)',
              color: 'var(--color-foreground)',
            },
            '.cm-scroller': { fontFamily: 'var(--font-mono)' },
            '.cm-gutters': {
              backgroundColor: 'var(--color-muted)',
              color: 'var(--color-muted-foreground)',
              border: 'none',
            },
            '.cm-activeLine, .cm-activeLineGutter': { backgroundColor: 'var(--color-accent)' },
            '.cm-cursor': { borderLeftColor: 'var(--color-foreground)' },
            '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
              backgroundColor: 'var(--color-secondary)',
            },
          }),
        ],
      }),
    })
    view.focus()
    return () => view.destroy()
    // created once per mount: `initial` seeds the document and is never
    // pushed into a live editor, which would move the cursor
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return <div ref={host} className="h-full min-h-96 overflow-hidden rounded-md border" />
}
