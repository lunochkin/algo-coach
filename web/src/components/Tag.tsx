import type { ReactNode } from 'react'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

// a short label beside a title, such as a problem's difficulty or a module's
// status: one shape wherever one reads
export function Tag({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <Badge variant="outline" className={cn('font-normal', className)}>
      {children}
    </Badge>
  )
}
