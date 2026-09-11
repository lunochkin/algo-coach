import { api, type Provider } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Button } from '@/components/ui/button'

const NAMES: Record<Provider, string> = { google: 'Google', github: 'GitHub' }

export function LoginPage() {
  const { data: offered, error } = useLoaded(
    (signal) => api.GET('/api/sign-in', { signal }),
    'sign-in',
  )

  if (error) return <p className="text-destructive">The sign-in did not load: {error}</p>
  if (!offered) return <p className="text-muted-foreground">Loading the sign-in…</p>

  const nothing = offered.providers.length === 0 && offered.dev_login === null
  return (
    <section className="mx-auto max-w-sm space-y-4 pt-16">
      <h1 className="text-2xl font-semibold">Sign in to algo-coach</h1>
      {nothing && <p className="text-muted-foreground">No sign-in is configured.</p>}
      {/* plain links, not the router's: each leaves the app for the API, which
          answers with a redirect */}
      {offered.providers.map((provider) => (
        <Button key={provider} className="w-full" asChild>
          <a href={`/api/auth/${provider}`}>Sign in with {NAMES[provider]}</a>
        </Button>
      ))}
      {offered.dev_login !== null && (
        <Button variant="outline" className="w-full" asChild>
          <a href="/api/auth/dev">Dev login as {offered.dev_login}</a>
        </Button>
      )}
    </section>
  )
}
