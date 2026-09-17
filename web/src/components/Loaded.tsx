import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'

type State<T> = { data?: T; error?: string; retry: () => void }

type Props<T> = {
  // what is loaded, as a page names it: "the board", "the card"
  of: string
  state: State<T>
  // the sentence for an answer carrying nothing, and what counts as nothing.
  // An array with no element is the default
  blank?: string
  blankWhen?: (data: T) => boolean
  children: (data: T) => ReactNode
}

// the three readings a page gives before its content, rendered once: a page
// that is loading, failed or empty then reads the same wherever the user is
export function Loaded<T>({ of, state, blank, blankWhen, children }: Props<T>) {
  if (state.error !== undefined)
    return (
      <div className="flex items-center gap-stack text-meta">
        <p className="text-destructive">
          {capitalised(of)} did not load: {state.error}
        </p>
        <Button variant="outline" size="sm" onClick={state.retry}>
          Retry
        </Button>
      </div>
    )
  if (state.data === undefined) return <p className="text-meta text-muted-foreground">Loading {of}…</p>
  if (blank !== undefined && (blankWhen ?? isEmpty)(state.data))
    return <p className="text-meta text-muted-foreground">{blank}</p>
  return <>{children(state.data)}</>
}

function isEmpty(data: unknown): boolean {
  return Array.isArray(data) && data.length === 0
}

function capitalised(of: string): string {
  return of.charAt(0).toUpperCase() + of.slice(1)
}
