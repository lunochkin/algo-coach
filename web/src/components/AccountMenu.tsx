import { LogOut, Menu } from 'lucide-react'

import { api, LOGIN, type Me } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

// revoked on the server, not only dropped from the browser, then to the login
async function signOut() {
  await api.DELETE('/api/session')
  window.location.assign(LOGIN)
}

// who the session signs in as, and the one act an account carries. The menu
// holds them rather than the navigation, which names where a page is
export function AccountMenu() {
  const me = useLoaded((signal) => api.GET('/api/me', { signal }), 'me')

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label="Your account">
          <Menu />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <div className="space-y-0.5 px-2 py-1.5">
          <p className={cn('font-medium', !me.data?.email && 'font-mono')}>{named(me.data)}</p>
          {/* the engine's own id, which every private record of theirs
              carries, and what the address is missing for where it is */}
          <p className="text-meta text-muted-foreground">
            {me.data === undefined ? (
              'Reading the session…'
            ) : me.data.email ? (
              <span className="font-mono">{me.data.user_id}</span>
            ) : (
              'Signed in with no provider linked'
            )}
          </p>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={signOut}>
          <LogOut />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// the address the provider verified, and the engine's own id where no
// provider linked one
function named(me: Me | undefined): string {
  if (me === undefined) return 'Signed in'
  return me.email ?? me.user_id
}
