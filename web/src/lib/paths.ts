import type { ProblemFrom } from '@climb/core'

// the page a problem was opened from, as the web addresses it
export function fromPath(from: ProblemFrom): string {
  switch (from.kind) {
    case 'card':
      return `/cards/${encodeURIComponent(from.slug)}`
    case 'listing':
      return '/problems'
    case 'technique':
      return `/techniques/${encodeURIComponent(from.technique)}`
    case 'board':
      return '/'
  }
}
