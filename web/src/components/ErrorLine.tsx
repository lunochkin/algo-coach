import type { ReactNode } from 'react'

// every refusal and failure a page reads, the same wherever it shows: a
// failed load, a refused press, a sync that did not reach the engine
export function ErrorLine({ children, title }: { children: ReactNode; title?: string }) {
  return (
    <p className="text-meta text-destructive" title={title}>
      {children}
    </p>
  )
}
