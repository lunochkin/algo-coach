import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import {
  bracketMatching,
  defaultHighlightStyle,
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

type Props = { initial: string; onChange: (code: string) => void }

// highlighting and indentation, and no `autocompletion()`: `flows.md` gives
// why the editor a sitting is typed into proposes nothing
export function CodeEditor({ initial, onChange }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const changed = useRef(onChange)
  changed.current = onChange

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
          syntaxHighlighting(defaultHighlightStyle),
          python(),
          keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
          EditorView.updateListener.of((update) => {
            if (update.docChanged) changed.current(update.state.doc.toString())
          }),
          EditorView.theme({
            '&': { height: '100%', fontSize: '14px' },
            '.cm-scroller': { fontFamily: 'var(--font-mono, ui-monospace, monospace)' },
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
