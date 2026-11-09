const KEY = 'algo-coach:theme'

export type Scheme = 'light' | 'dark'

// the scheme the viewer chose, or none where they never pressed the switch
export function chosen(): Scheme | null {
  try {
    const stored = localStorage.getItem(KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    return null
  }
}

export function preferred(): Scheme {
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// the root carries the scheme as an attribute: `light-dark()` reads it off
// `color-scheme`, and the `dark` variant reads the attribute itself
export function apply(scheme: Scheme): void {
  document.documentElement.dataset.theme = scheme
}

export function choose(scheme: Scheme): void {
  apply(scheme)
  try {
    localStorage.setItem(KEY, scheme)
  } catch {
    // a browser refusing storage costs the choice on reload, not the page
  }
}

// a viewer who never pressed the switch follows their browser, and follows it
// while the page is open
export function follow(): () => void {
  const media = matchMedia('(prefers-color-scheme: dark)')
  const moved = () => chosen() === null && apply(preferred())
  media.addEventListener('change', moved)
  return () => media.removeEventListener('change', moved)
}
