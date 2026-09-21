import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import {
  bracketMatching,
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
import { useEffect, useRef } from 'react'

import { HIGHLIGHTER } from '@/lib/python'

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
          syntaxHighlighting(HIGHLIGHTER),
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

  return <div ref={host} className="h-full min-h-96 overflow-hidden rounded-xl border" />
}
