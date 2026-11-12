import 'katex/dist/katex.min.css'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import type { Components } from 'react-markdown'
import { codeWraps } from '@algo-coach/core'

import { WrappedText } from '@/components/PythonCode'

// authored and generated prose: a card's brief, a template's notes and a
// statement, tables and `$…$` math included
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{ pre: CodeFence }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

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
