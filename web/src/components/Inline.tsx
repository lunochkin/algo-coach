import { spans } from '@algo-coach/core'

// authored prose inside a paragraph, its backtick pairs drawn as a lesson draws inline code
export function Inline({ text }: { text: string }) {
  return (
    <>
      {spans(text).map((s, i) =>
        s.code ? (
          <code key={i} className="code-inline">
            {s.text}
          </code>
        ) : (
          s.text
        ),
      )}
    </>
  )
}
