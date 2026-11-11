import {
  SECTION_PRACTICE,
  SECTION_PROBLEMS,
  SECTION_CARDS,
  SECTION_KNOWLEDGE,
} from '@algo-coach/core'
import { useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router'

import { AccountMenu } from '@/components/AccountMenu'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// the four the navigation names. A technique and a picked problem, which
// holds its sitting, are steps down from the board, so Practice stays marked
const SECTIONS = [
  {
    label: SECTION_PRACTICE,
    to: '/',
    owns: (path: string) =>
      path === '/' || path.startsWith('/techniques/') || path.startsWith('/problems/'),
  },
  // the listing alone: a picked problem is a step down from the board, from a
  // technique or from a card, and the section it sits under cannot say which
  { label: SECTION_PROBLEMS, to: '/problems', owns: (path: string) => path === '/problems' },
  { label: SECTION_CARDS, to: '/cards', owns: (path: string) => path.startsWith('/cards') },
  {
    label: SECTION_KNOWLEDGE,
    to: '/knowledge',
    owns: (path: string) => path === '/knowledge' || path.startsWith('/knowledge/'),
  },
]

export function NavMenu({ wide }: { wide: boolean }) {
  const { pathname } = useLocation()
  const sections = useRef<HTMLDivElement>(null)

  // a phone's width holds three of the four, so the marked one is scrolled to
  useEffect(() => {
    const row = sections.current
    const marked = row?.querySelector('[aria-current="page"]')
    if (!row || !marked) return
    // the row alone scrolls: scrollIntoView would move the page sideways too
    const over = marked.getBoundingClientRect().right - row.getBoundingClientRect().right
    if (over > 0) row.scrollLeft += over
  }, [pathname])

  return (
    <header className="border-b">
      <nav
        className={cn(
          'mx-auto flex items-center gap-1 px-gutter py-2',
          wide ? 'max-w-wide' : 'max-w-reading',
        )}
      >
        {/* the wordmark reaches the board, as a site's own name does */}
        <Link
          to="/"
          className={cn(
            'mr-1 flex shrink-0 items-center gap-2 whitespace-nowrap sm:mr-4',
            'font-semibold underline-offset-4 hover:underline',
          )}
        >
          {/* the flame dot the site's wordmark carries, and alone at phone
              width, where the four sections need the room */}
          <span aria-hidden className="size-2.5 rounded-full bg-brand" />
          <span className="sr-only sm:not-sr-only">algo-coach</span>
        </Link>
        <div ref={sections} className="flex min-w-0 items-center gap-1 overflow-x-auto">
          {SECTIONS.map(({ label, to, owns }) => {
            const current = owns(pathname)
            return (
              <Button key={to} variant={current ? 'secondary' : 'ghost'} size="sm" asChild>
                <Link to={to} aria-current={current ? 'page' : undefined}>
                  {label}
                </Link>
              </Button>
            )
          })}
        </div>
        <div className="ml-auto flex shrink-0 items-center gap-1">
          <ThemeToggle />
          <AccountMenu />
        </div>
      </nav>
    </header>
  )
}
