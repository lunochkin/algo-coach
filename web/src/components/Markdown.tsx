import 'katex/dist/katex.min.css'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

// authored and generated prose: a card's brief, a template's notes and a
// statement, tables and `$…$` math included
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-neutral max-w-none dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
