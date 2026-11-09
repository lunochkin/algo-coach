import { ChevronLeft } from 'lucide-react'
import { Link } from 'react-router'

import { Button } from '@/components/ui/button'

// the way back a page names: the page the user came from
export function BackLink({ to, label }: { to: string; label: string }) {
  return (
    <Button variant="link" size="sm" className="h-auto px-0 text-muted-foreground" asChild>
      <Link to={to}>
        <ChevronLeft className="size-4" />
        {label}
      </Link>
    </Button>
  )
}
