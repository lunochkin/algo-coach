import 'katex/dist/katex.min.css'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import type { Components } from 'react-markdown'
import { Children, isValidElement, type ReactNode } from 'react'
import { codeWraps, EXTERNAL_HINT, EXTERNAL_MARK, isExternal, tableShape } from '@algo-coach/core'

import { WrappedText } from '@/components/PythonCode'
import { useColumns } from '@/lib/columns'

// authored and generated prose: a card's brief, a template's notes and a
// statement, tables and `$…$` math included
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{ pre: CodeFence, a: ProseLink, table: ProseTable }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

// a link leaving the app opens a tab and carries the mark: `pages.md`, The design system
export const ProseLink = ({ href = '', children }: { href?: string; children?: ReactNode }) =>
  isExternal(href) ? (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
      <span aria-hidden>{EXTERNAL_MARK}</span>
      <span className="sr-only"> ({EXTERNAL_HINT.toLowerCase()})</span>
    </a>
  ) : (
    <a href={href}>{children}</a>
  )

type Hast = { type: string; tagName?: string; value?: string; properties?: { className?: unknown }; children?: Hast[] }

const textOf = (n: Hast): string => n.value ?? (n.children ?? []).map(textOf).join('')

// a fenced block wraps where its fence names a language: `pages.md`, The design system
export const CodeFence: Components['pre'] = ({ node, children }) => {
  const code = (node as Hast | undefined)?.children?.find((x) => x.tagName === 'code')
  const classes = code?.properties?.className
  const lang = (Array.isArray(classes) ? classes : [])
    .map(String)
    .find((x) => x.startsWith('language-'))
    ?.slice('language-'.length)
  if (!code || !codeWraps(lang)) return <pre>{children}</pre>
  return (
    <pre className="whitespace-pre">
      <code className={`language-${lang}`}>
        <WrappedText code={textOf(code)} />
      </code>
    </pre>
  )
}

// a character of prose, averaged over ordinary words
const PROSE_PROBE = 'the quick brown fox jumps over the lazy dog'

const kids = (n: ReactNode): ReactNode[] =>
  isValidElement(n) ? Children.toArray((n.props as { children?: ReactNode }).children) : []

// a table's cells as rendered, rows below the header's, read in the order
// the hast node holds them
function cellsOf(children: ReactNode): ReactNode[][] {
  return Children.toArray(children)
    .flatMap(kids)
    .filter(isValidElement)
    .map((tr) => kids(tr).filter(isValidElement).map((cell) => kids(cell)))
}

const textRows = (n: Hast): string[][] =>
  (n.children ?? [])
    .filter((x) => x.tagName === 'thead' || x.tagName === 'tbody')
    .flatMap((part) => (part.children ?? []).filter((tr) => tr.tagName === 'tr'))
    .map((tr) => (tr.children ?? []).filter((c) => c.tagName === 'th' || c.tagName === 'td').map(textOf))

// a grid where the columns fit, and a block per row where they do not: `pages.md`, The design system
export const ProseTable: Components['table'] = ({ node, children }) => {
  const { ref, cols } = useColumns(PROSE_PROBE)
  const [header = [], ...rows] = node ? textRows(node as Hast) : []
  const grid = tableShape(header, rows, cols) === 'grid'
  const [head = [], ...body] = grid ? [] : cellsOf(children)
  return (
    <div ref={ref as React.RefObject<HTMLDivElement>} className={grid ? undefined : 'table-rows space-y-3'}>
      {grid ? (
        <table>{children}</table>
      ) : (
        body.map((row, i) => (
          <div key={i} className="border-l-2 border-border pl-3">
            <div className="font-medium">{row[0]}</div>
            {row.slice(1).map((cell, j) => (
              <div key={j}>
                {header[j + 1]?.trim() && <span className="text-muted-foreground">{head[j + 1]}: </span>}
                {cell}
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  )
}

