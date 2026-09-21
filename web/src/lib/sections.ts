import { useEffect, useState } from 'react'

export type Item = { id: string; label: string }

// the section the reader is in, read from where each one sits rather than
// from the scroll position, so a collapsed section moves the mark with it
export function useCurrent(ids: string[]): string | null {
  const [current, setCurrent] = useState<string | null>(null)
  const key = ids.join(',')

  useEffect(() => {
    const named = key.split(',')
    const visible = new Set<string>()
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) visible.add(entry.target.id)
          else visible.delete(entry.target.id)
        }
        setCurrent(named.find((id) => visible.has(id)) ?? null)
      },
      // the band under the bar: a section counts as current while its top
      // third of the window holds it
      { rootMargin: '-56px 0px -66% 0px' },
    )
    for (const id of named) {
      const element = document.getElementById(id)
      if (element) observer.observe(element)
    }
    return () => observer.disconnect()
  }, [key])

  return current
}
