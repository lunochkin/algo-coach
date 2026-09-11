import { Link, useLocation } from 'react-router'

import { Button } from '@/components/ui/button'

// a technique and a picked problem are steps down from the board, so the board
// stays marked while the user is on them
const SECTIONS = [
  { label: 'Board', to: '/', owns: (path: string) => path === '/' || path.startsWith('/techniques/') },
  { label: 'Cards', to: '/cards', owns: (path: string) => path.startsWith('/cards') },
]

export function NavMenu() {
  const { pathname } = useLocation()

  return (
    <header className="border-b">
      <nav className="mx-auto flex max-w-4xl items-center gap-1 px-6 py-2">
        <span className="mr-4 font-semibold">algo-coach</span>
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
      </nav>
    </header>
  )
}
