import type { ReactNode } from 'react'

import { SectionHeading } from '@/components/SectionHeading'
import { cn } from '@/lib/utils'

// the heading is the press that closes its own section, and the bar above
// reaches every one of them by id
export function PageSection({
  id,
  title,
  count,
  aside,
  sub = false,
  body = 'prose',
  closed,
  onToggle,
  children,
}: {
  id: string
  title: string
  count?: number
  // a section inside another, as a module's lessons sit under the module
  sub?: boolean
  aside?: ReactNode
  // the panel the body sits in: prose padded, rows edge to edge, or none
  // where the body brings panels of its own
  body?: 'prose' | 'rows' | 'bare'
  closed: boolean
  onToggle: (id: string) => void
  children: ReactNode
}) {
  return (
    // a heading over a bordered panel, as every page's sections read: a brief
    // carrying headings of its own then reads inside one of them
    <section id={id} className="scroll-mt-16 space-y-stack">
      <SectionHeading
        sub={sub}
        title={title}
        count={count}
        aside={aside}
        closed={closed}
        onToggle={() => onToggle(id)}
      />
      {!closed &&
        (body === 'bare' ? (
          children
        ) : (
          <div
            className={cn(
              'rounded-xl border bg-card',
              body === 'prose' ? 'px-4 py-3' : 'overflow-hidden',
            )}
          >
            {children}
          </div>
        ))}
    </section>
  )
}
