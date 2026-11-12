import type { ReactNode } from 'react'

import { SectionHeading } from '@/components/SectionHeading'

// the heading is the press that closes its own section, and the bar above
// reaches every one of them by id
export function PageSection({
  id,
  title,
  count,
  aside,
  sub = false,
  body = 'prose',
  closed = false,
  onToggle,
  children,
}: {
  id: string
  title: string
  count?: number
  // a section inside another, as a module's lessons sit under the module
  sub?: boolean
  aside?: ReactNode
  // rows sit in a panel edge to edge. Prose reads bare under its heading, so
  // a code block in it is the only box, and `bare` is a body bringing panels
  // of its own
  body?: 'prose' | 'rows' | 'bare'
  // without onToggle the section does not close, as the board's sections do not
  closed?: boolean
  onToggle?: (id: string) => void
  children: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-16 space-y-stack">
      <SectionHeading
        sub={sub}
        title={title}
        count={count}
        aside={aside}
        closed={closed}
        onToggle={onToggle && (() => onToggle(id))}
      />
      {!closed &&
        (body === 'rows' ? (
          <div className="overflow-hidden rounded-xl border bg-card">{children}</div>
        ) : (
          children
        ))}
    </section>
  )
}
