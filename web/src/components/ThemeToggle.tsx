import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { choose, chosen, follow, preferred, type Scheme } from '@/lib/theme'

// the one setting the app keeps, and the browser keeps it: no store holds a
// user's settings
export function ThemeToggle() {
  const [scheme, setScheme] = useState<Scheme>(() => chosen() ?? preferred())

  useEffect(follow, [])

  function toggle() {
    const next: Scheme = scheme === 'dark' ? 'light' : 'dark'
    choose(next)
    setScheme(next)
  }

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={toggle}
      aria-label={scheme === 'dark' ? 'Read in light' : 'Read in dark'}
    >
      {scheme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  )
}
