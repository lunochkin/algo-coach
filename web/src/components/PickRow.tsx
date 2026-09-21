import type { ReactNode } from 'react'
import { Link } from 'react-router'

type Props = {
  to: string
  title: string
  // the badge beside the title: a difficulty, a requiredness
  badge?: ReactNode
  // the counts, right-aligned: each a label and its reading
  stats: { label: string; value: ReactNode }[]
}

// one pick on a list of picks: a technique on the board, a problem under a
// technique. The whole row is the link, so the pointer never hunts for the
// title, and the counts read as one cluster rather than as four columns
export function PickRow({ to, title, badge, stats }: Props) {
  return (
    <Link
      to={to}
      className="group -mx-3 flex items-center gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-accent"
    >
      <span className="min-w-0 font-medium underline-offset-4 group-hover:underline">
        {title}
      </span>
      {badge}
      <span className="ml-auto flex shrink-0 items-center gap-5 text-meta text-muted-foreground">
        {stats.map((stat) => (
          <span key={stat.label} className="flex items-baseline gap-1.5">
            <span className="tabular-nums text-foreground">{stat.value}</span>
            {stat.label}
          </span>
        ))}
      </span>
    </Link>
  )
}

// the rows of one list, divided by a hairline
export function PickList({ children }: { children: ReactNode }) {
  return <div className="divide-y divide-border">{children}</div>
}
