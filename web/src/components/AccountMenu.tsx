import { LogOut, Menu, Settings, Smartphone } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { named, signOut } from '@/api/account'
import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { SignedInApps } from '@/components/SignedInApps'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

// who the session signs in as, the settings, the apps signed in as it, and
// the sign-out.
// The menu holds them rather than the navigation, which names where a page is
export function AccountMenu() {
  const me = useLoaded((signal) => api.GET('/api/me', { signal }), 'me')
  const [apps, setApps] = useState(false)

  return (
    <>
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
          <DropdownMenuItem asChild>
            <Link to="/settings">
              <Settings />
              Settings
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => setApps(true)}>
            <Smartphone />
            Signed-in apps
          </DropdownMenuItem>
          <DropdownMenuItem onClick={signOut}>
            <LogOut />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <SignedInApps open={apps} onOpenChange={setApps} />
    </>
  )
}
