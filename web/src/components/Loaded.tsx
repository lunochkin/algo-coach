import { RETRY, pageReading } from '@algo-coach/core'
import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'

import { ErrorLine } from '@/components/ErrorLine'

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
  const shown = pageReading(of, state, blank, blankWhen)
  if (shown.kind === 'failed')
    return (
      <div className="flex items-center gap-stack text-meta">
        <ErrorLine>{shown.line}</ErrorLine>
        <Button variant="outline" size="sm" onClick={state.retry}>
          {RETRY}
        </Button>
      </div>
    )
  if (shown.kind !== 'content')
    return <p className="text-meta text-muted-foreground">{shown.line}</p>
  return <>{children(shown.data)}</>
}
