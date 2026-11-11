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

// a long page's sections: which the reader closed, the one they are in, and
// a jump that opens a section before scrolling to it, since a closed one
// would land on its heading with nothing under it. Nothing is closed until
// the reader closes it, and a reload opens every one again
export function useSections(items: Item[]) {
  const [closed, setClosed] = useState<string[]>([])
  const current = useCurrent(items.map((item) => item.id))
  return {
    items,
    current,
    closed: (id: string) => closed.includes(id),
    toggle: (id: string) =>
      setClosed(closed.includes(id) ? closed.filter((one) => one !== id) : [...closed, id]),
    jump: (id: string) => {
      setClosed(closed.filter((one) => one !== id))
      requestAnimationFrame(() =>
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }),
      )
    },
  }
}

export type Sections = ReturnType<typeof useSections>
