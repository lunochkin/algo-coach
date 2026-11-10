import 'katex/dist/katex.min.css'
import { Children, isValidElement, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import { Link } from 'react-router'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

import { anchor } from '@algo-coach/core'

import { lessonPath } from '@/knowledge/paths'

// a lesson's Markdown: its `lesson:` links stay in the app, and each heading
// carries the anchor a link names, as the core reads them
export function LessonText({ module, text }: { module: string; text: string }) {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h2: ({ children }) => <h2 id={anchor(plain(children))}>{children}</h2>,
          h3: ({ children }) => <h3 id={anchor(plain(children))}>{children}</h3>,
          a: ({ href = '', children }) => {
            if (!href.startsWith('lesson:')) return <a href={href}>{children}</a>
            const [slug, part = ''] = href.slice('lesson:'.length).split('#')
            return <Link to={lessonPath(module, slug, part)}>{children}</Link>
          },
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}

function plain(children: ReactNode): string {
  return Children.toArray(children)
    .map((child) =>
      typeof child === 'string' || typeof child === 'number'
        ? String(child)
        : isValidElement<{ children?: ReactNode }>(child)
          ? plain(child.props.children)
          : '',
    )
    .join('')
}
