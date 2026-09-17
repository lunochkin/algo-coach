import type { ReactNode } from 'react'

import { BackLink } from '@/components/BackLink'

type Props = {
  // the page the user came from, named by it. A section's root page carries
  // none, since the navigation reaches that page in one press
  back?: { to: string; label: string }
  title: ReactNode
  // the one line identifying what the title names
  note?: ReactNode
}

export function PageHeader({ back, title, note }: Props) {
  return (
    <header className="space-y-1">
      {back && <BackLink {...back} />}
      <h1 className="text-title font-semibold">{title}</h1>
      {note && <div className="text-meta text-muted-foreground">{note}</div>}
    </header>
  )
}
