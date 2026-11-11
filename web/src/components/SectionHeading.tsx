import { ChevronDown } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

// a section's heading and how many records it holds, the same on every page.
// `sub` heads a section inside another, as a module's lessons sit under the
// module; `aside` holds the section's own presses or reading, at the right.
// With `onToggle` the heading is the press that closes its own section
export function SectionHeading({
  title,
  count,
  aside,
  sub = false,
  closed,
  onToggle,
}: {
  title: ReactNode
  count?: number
  aside?: ReactNode
  sub?: boolean
  closed?: boolean
  onToggle?: () => void
}) {
  const Tag = sub ? 'h3' : 'h2'
  const text = (
    <>
      {onToggle && (
        <ChevronDown
          aria-hidden="true"
          className={cn('size-4 self-center transition-transform', closed && '-rotate-90')}
        />
      )}
      {title}
      {count !== undefined && (
        <span className="text-meta font-normal text-muted-foreground tabular-nums">{count}</span>
      )}
    </>
  )
  return (
    <div className="flex items-baseline gap-3">
      <Tag className={cn('font-medium', sub ? 'text-body' : 'text-heading')}>
        {onToggle ? (
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={!closed}
            className="flex items-baseline gap-2"
          >
            {text}
          </button>
        ) : (
          <span className="flex items-baseline gap-2">{text}</span>
        )}
      </Tag>
      {aside && (
        <div className="ml-auto flex items-baseline gap-stack text-meta text-muted-foreground">
          {aside}
        </div>
      )}
    </div>
  )
}
