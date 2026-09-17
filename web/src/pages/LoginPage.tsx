import { Link, useSearchParams } from 'react-router'

import { api, PRIVACY, type Provider } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Button } from '@/components/ui/button'

const NAMES: Record<Provider, string> = { google: 'Google', github: 'GitHub' }

// the codes `Refusal` in `api/signin.py` sends back, as sentences. The code
// carries no address, so a refusal names none
const REFUSALS: Record<string, string> = {
  incomplete: 'That sign-in did not complete. Try again.',
  'no-email': 'That account has no verified email address, which signs nobody in.',
  uninvited: 'That address has no invitation.',
}

export function LoginPage() {
  const offered = useLoaded((signal) => api.GET('/api/sign-in', { signal }), 'sign-in')
  const [search] = useSearchParams()
  const refused = search.get('refused')

  return (
    <section className="mx-auto max-w-form space-y-stack pt-16">
      <h1 className="text-title font-semibold">Sign in to algo-coach</h1>
      {refused !== null && (
        <p className="text-destructive">
          {REFUSALS[refused] ?? 'That sign-in did not complete. Try again.'}
        </p>
      )}
      <Loaded
        of="the sign-in"
        state={offered}
        blank="No sign-in is configured."
        blankWhen={(one) => one.providers.length === 0 && one.dev_login === null}
      >
        {(offered) => (
          <div className="space-y-stack">
            {/* plain links, not the router's: each leaves the app for the API,
                which answers with a redirect */}
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
          </div>
        )}
      </Loaded>
      <p className="text-meta text-muted-foreground">
        <Link to={PRIVACY} className="underline underline-offset-4">
          Privacy policy
        </Link>
      </p>
    </section>
  )
}
