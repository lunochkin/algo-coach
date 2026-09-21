import { Link, useLocation } from 'react-router'

import { api, LOGIN } from '@/api/client'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// the two sections `pages.md` names. A technique, a picked problem and a
// sitting are steps down from the board, so Practice stays marked on them
const SECTIONS = [
  {
    label: 'Practice',
    to: '/',
    owns: (path: string) =>
      path === '/' ||
      path.startsWith('/techniques/') ||
      path.startsWith('/problems/') ||
      path.startsWith('/sittings/'),
  },
  { label: 'Cards', to: '/cards', owns: (path: string) => path.startsWith('/cards') },
]

// revoked on the server, not only dropped from the browser, then to the login
async function signOut() {
  await api.DELETE('/api/session')
  window.location.assign(LOGIN)
}

export function NavMenu({ wide }: { wide: boolean }) {
  const { pathname } = useLocation()

  return (
    <header className="border-b">
      <nav
        className={cn(
          'mx-auto flex items-center gap-1 px-gutter py-2',
          wide ? 'max-w-wide' : 'max-w-reading',
        )}
      >
        {/* the wordmark reaches the board, as a site's own name does */}
        <Link to="/" className="mr-4 font-semibold underline-offset-4 hover:underline">
          algo-coach
        </Link>
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
        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </nav>
    </header>
  )
}
