import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// authored prose: a card's brief and a template's notes, tables included
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-neutral max-w-none dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
