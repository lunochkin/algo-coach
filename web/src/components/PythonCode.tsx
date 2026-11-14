import { codeRows, WRAP_MARK, type CodeRow } from '@climb/core'
import { pieces } from '@climb/editor'
import { type ReactNode } from 'react'

import { useColumns } from '@/lib/columns'

// each wrapped part opens on a mark no copy carries: `pages.md`, The design system
function Rows({ rows, body }: { rows: CodeRow[]; body: (row: CodeRow) => ReactNode }) {
  return (
    <span className="block" onCopy={copyRows}>
      {rows.map((row, i) => (
        <span key={i} className="block" data-row data-cont={row.cont ? '' : undefined}>
          {row.cont ? (
            <span data-wrap aria-hidden className="select-none">
              {row.indent}
              <span className="text-muted-foreground">{WRAP_MARK}</span>
            </span>
          ) : (
            row.indent
          )}
          {body(row)}
          <span className="hidden">{row.gap}</span>
        </span>
      ))}
    </span>
  )
}

// a wrap is drawn, never copied: the rows a selection covers are joined back
// into their lines, as an editor's soft wrap copies
function copyRows(e: React.ClipboardEvent<HTMLElement>) {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return
  const range = sel.getRangeAt(0)
  // a selection reaching past the block keeps the browser's own copy
  if (!e.currentTarget.contains(range.commonAncestorContainer)) return
  let out = ''
  let first = true
  for (const row of e.currentTarget.querySelectorAll<HTMLElement>('[data-row]')) {
    if (!range.intersectsNode(row)) continue
    const part = document.createRange()
    part.selectNodeContents(row)
    if (range.compareBoundaryPoints(Range.START_TO_START, part) > 0)
      part.setStart(range.startContainer, range.startOffset)
    if (range.compareBoundaryPoints(Range.END_TO_END, part) < 0)
      part.setEnd(range.endContainer, range.endOffset)
    const copy = part.cloneContents()
    copy.querySelectorAll('[data-wrap]').forEach((x) => x.remove())
    out += (first || row.dataset.cont !== undefined ? '' : '\n') + (copy.textContent ?? '')
    first = false
  }
  e.clipboardData.setData('text/plain', out)
  e.preventDefault()
}

const BLOCK = 'rounded-md bg-muted p-3 font-mono text-code whitespace-pre'

// Python read on a page, coloured by the one mapping the editor uses:
// `pages.md`, The design system
export function PythonCode({ code }: { code: string }) {
  const { ref, cols } = useColumns()
  const lines = byLine(code)
  return (
    <pre ref={ref as React.RefObject<HTMLPreElement>} className={`relative ${BLOCK}`}>
      <code>
        <Rows rows={codeRows(code, cols)} body={(row) => slice(lines[row.line] ?? [], row.from, row.text.length)} />
      </code>
    </pre>
  )
}

type Piece = { token?: string; text: string }

// the coloured pieces regrouped by line, the indent dropped, since a row draws it
function byLine(code: string): Piece[][] {
  const lines: Piece[][] = [[]]
  for (const piece of pieces(code.replace(/\s+$/, '')))
    piece.text.split('\n').forEach((text, j) => {
      if (j > 0) lines.push([])
      if (text) lines[lines.length - 1].push({ token: piece.token, text })
    })
  return lines.map((line) => {
    const indent = /^[ \t]*/.exec(line.map((p) => p.text).join(''))![0].length
    return cut(line, indent, Infinity)
  })
}

function cut(line: Piece[], from: number, length: number): Piece[] {
  const out: Piece[] = []
  let at = 0
  for (const piece of line) {
    const start = Math.max(from - at, 0)
    const end = Math.min(from + length - at, piece.text.length)
    if (end > start) out.push({ token: piece.token, text: piece.text.slice(start, end) })
    at += piece.text.length
  }
  return out
}

function slice(line: Piece[], from: number, length: number): ReactNode {
  return cut(line, from, length).map((piece, i) => (
    <span key={i} className={piece.token}>
      {piece.text}
    </span>
  ))
}

// code read in a lesson, a statement or a detail, wrapped without colours
export function WrappedText({ code }: { code: string }) {
  const { ref, cols } = useColumns()
  return (
    <span ref={ref as React.RefObject<HTMLSpanElement>} className="relative block">
      <Rows rows={codeRows(code, cols)} body={(row) => row.text} />
    </span>
  )
}

// the cover over a hidden form: a dashed press naming the form's length and
// nothing of it, so a reader decides from that whether to try recalling it
export function RevealPress({ label, onReveal }: { label: string; onReveal: () => void }) {
  return (
    <button
      type="button"
      onClick={onReveal}
      className="w-full rounded-md border border-dashed px-3 py-2 text-left text-meta text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      {label}
    </button>
  )
}

// a value read back, such as a failing case's arguments or a question's code:
// the code block's shape without Python's colours
export function PlainCode({ children, wrap = false }: { children: string; wrap?: boolean }) {
  return wrap ? (
    <pre className={`max-h-64 overflow-y-auto ${BLOCK}`}>
      <WrappedText code={children} />
    </pre>
  ) : (
    <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">{children}</pre>
  )
}
