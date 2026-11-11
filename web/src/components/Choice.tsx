import type { ReactNode } from 'react'

import { SectionHeading } from '@/components/SectionHeading'

// one choice of a form: its label as a small heading, then its toggles, as
// the start sheet and the exam both ask
export function Choice({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1">
      <SectionHeading sub title={label} />
      {children}
    </div>
  )
}
