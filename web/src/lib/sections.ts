import { useEffect, useState } from 'react'

import { sectionOpened, sectionToggled } from '@algo-coach/core'

export type Item = { id: string; label: string }

// the section the reader is in, read from where each one sits rather than
// from the scroll position, so a collapsed section moves the mark with it
export function useCurrent(ids: string[]): string | null {
  const [current, setCurrent] = useState<string | null>(null)
  const key = ids.join(',')

  useEffect(() => {
    const named = key.split(',')
    const visible = new Set<string>()
    // at the end the last section is read, though its top never reaches the band
    const atEnd = () =>
      window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2
    const read = () =>
      setCurrent(atEnd() ? (named.at(-1) ?? null) : (named.find((id) => visible.has(id)) ?? null))
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) visible.add(entry.target.id)
          else visible.delete(entry.target.id)
        }
        read()
      },
      // the band under the bar: a section counts as current while its top
      // third of the window holds it
      { rootMargin: '-56px 0px -66% 0px' },
    )
    for (const id of named) {
      const element = document.getElementById(id)
      if (element) observer.observe(element)
    }
    window.addEventListener('scroll', read, { passive: true })
    return () => {
      observer.disconnect()
      window.removeEventListener('scroll', read)
    }
  }, [key])

  return current
}

// a long page's sections: which the reader closed, the one they are in, and
// a jump that opens a section before scrolling to it, since a closed one
// would land on its heading with nothing under it. Nothing is closed until
// the reader closes it, and a reload opens every one again
export function useSections(items: Item[]) {
  const [closed, setClosed] = useState<string[]>([])
  const read = useCurrent(items.map((item) => item.id))
  // the section pressed stays marked until the reader scrolls by hand: a jump
  // near the end lands where the end rule would mark the last section instead
  const [jumped, setJumped] = useState<string | null>(null)
  useEffect(() => {
    if (!jumped) return
    const release = () => setJumped(null)
    const events = ['wheel', 'touchstart', 'keydown'] as const
    for (const e of events) window.addEventListener(e, release, { passive: true })
    return () => {
      for (const e of events) window.removeEventListener(e, release)
    }
  }, [jumped])
  return {
    items,
    current: jumped ?? read,
    closed: (id: string) => closed.includes(id),
    toggle: (id: string) => setClosed((was) => sectionToggled(was, id)),
    jump: (id: string) => {
      setClosed((was) => sectionOpened(was, id))
      setJumped(id)
      requestAnimationFrame(() =>
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }),
      )
    },
  }
}

export type Sections = ReturnType<typeof useSections>
