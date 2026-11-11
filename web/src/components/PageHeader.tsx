import type { ReactNode } from 'react'

import { BackLink } from '@/components/BackLink'

type Props = {
  // the page the user came from, named by it. A section's root page carries
  // none, since the navigation reaches that page in one press
  back?: { to: string; label: string }
  title: ReactNode
  // the one line identifying what the title names
  note?: ReactNode
  // beside the title: a running queue's score and its Stop
  aside?: ReactNode
}

// drawn outside the page's readings, so a page loading or failed still names
// itself and its way back: `pages.md`, A page's areas
export function PageHeader({ back, title, note, aside }: Props) {
  return (
    <header className="space-y-1">
      {back && <BackLink {...back} />}
      <div className="flex items-center gap-stack">
        <h1 className="flex-1 text-title font-semibold">{title}</h1>
        {aside}
      </div>
      {note && <div className="text-meta text-muted-foreground">{note}</div>}
    </header>
  )
}
