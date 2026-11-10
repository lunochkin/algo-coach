import { LogOut, Menu, Settings, Smartphone } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import {
  named,
  NO_PROVIDER_LINKED,
  READING_SESSION,
  SETTINGS,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  YOUR_ACCOUNT,
} from '@algo-coach/core'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { SignedInDevices } from '@/components/SignedInDevices'
import { SignOut } from '@/components/SignOut'
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

  // the confirmation sits outside the menu, which unmounts as it closes
  return (
    <SignOut>
      {(start) => (
        <>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon-sm" aria-label={YOUR_ACCOUNT}>
                <Menu />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <div className="space-y-0.5 px-2 py-1.5">
                <p className={cn('font-medium', !me.data?.email && 'font-mono')}>
                  {named(me.data)}
                </p>
                {/* the engine's own id, which every private record of theirs
                carries, and what the address is missing for where it is */}
                <p className="text-meta text-muted-foreground">
                  {me.data === undefined ? (
                    READING_SESSION
                  ) : me.data.email ? (
                    <span className="font-mono">{me.data.user_id}</span>
                  ) : (
                    NO_PROVIDER_LINKED
                  )}
                </p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/settings">
                  <Settings />
                  {SETTINGS}
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => setApps(true)}>
                <Smartphone />
                {SIGNED_IN_DEVICES}
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={start}>
                <LogOut />
                {SIGN_OUT}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <SignedInDevices open={apps} onOpenChange={setApps} />
        </>
      )}
    </SignOut>
  )
}
