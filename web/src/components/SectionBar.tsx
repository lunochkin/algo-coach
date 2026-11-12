import { useEffect, useRef, useState } from 'react'

import type { Item } from '@/lib/sections'
import { cn } from '@/lib/utils'

// the sections of a long page, in one row that stays at the top as the page
// scrolls: a card's brief runs past a screen, and the ladder under it is
// otherwise reached by scrolling through the whole of it
export function SectionBar({
  items,
  current,
  onJump,
}: {
  items: Item[]
  current: string | null
  onJump: (id: string) => void
}) {
  const row = useRef<HTMLDivElement>(null)
  const [more, setMore] = useState({ left: false, right: false })

  // the row follows the marked section, as the navigation does: `pages.md`
  useEffect(() => {
    const el = row.current
    const marked = el?.querySelector<HTMLElement>('[aria-current="true"]')
    if (!el || !marked) return
    const pad = 24
    // the row alone scrolls: scrollIntoView would move the page sideways too
    const left = marked.offsetLeft - pad
    const right = marked.offsetLeft + marked.offsetWidth + pad - el.clientWidth
    if (el.scrollLeft > left) el.scrollTo({ left, behavior: 'smooth' })
    else if (el.scrollLeft < right) el.scrollTo({ left: right, behavior: 'smooth' })
  }, [current])

  // a faded edge says the row goes on past it
  useEffect(() => {
    const el = row.current
    if (!el) return
    const read = () =>
      setMore({
        left: el.scrollLeft > 1,
        right: el.scrollLeft + el.clientWidth < el.scrollWidth - 1,
      })
    read()
    el.addEventListener('scroll', read, { passive: true })
    const observer = new ResizeObserver(read)
    observer.observe(el)
    return () => {
      el.removeEventListener('scroll', read)
      observer.disconnect()
    }
  }, [items])

  // one section has nothing to jump between
  if (items.length < 2) return null
  const fade = `linear-gradient(to right, ${more.left ? 'transparent' : 'black'}, black 2rem, black calc(100% - 2rem), ${more.right ? 'transparent' : 'black'})`
  return (
    <nav className="sticky top-0 z-10 -mx-gutter border-b bg-background px-gutter">
      <div
        ref={row}
        className="relative flex gap-1 overflow-x-auto py-2 [scrollbar-width:none]"
        style={{ maskImage: fade, WebkitMaskImage: fade }}
      >
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onJump(item.id)}
            aria-current={current === item.id ? 'true' : undefined}
            className={cn(
              'rounded-lg px-2.5 py-1 text-meta whitespace-nowrap transition-colors',
              current === item.id
                ? 'bg-secondary text-secondary-foreground'
                : 'text-muted-foreground hover:bg-accent',
            )}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
