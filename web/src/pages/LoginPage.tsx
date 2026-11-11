import { Link, useSearchParams } from 'react-router'

import {
  continueWith,
  devLoginAs,
  LOGIN_INTRO,
  NO_SIGN_IN,
  refusal,
  PRIVACY_LINK,
  PRIVACY_NOTE,
  SIGN_IN_TITLE,
  OF,
} from '@algo-coach/core'

import { api, PRIVACY } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { ErrorLine } from '@/components/ErrorLine'
import { Loaded } from '@/components/Loaded'
import { Button } from '@/components/ui/button'

export function LoginPage() {
  const offered = useLoaded((signal) => api.GET('/api/sign-in', { signal }), 'sign-in')
  const [search] = useSearchParams()
  const refused = search.get('refused')

  return (
    <section className="mx-auto max-w-form space-y-section py-16">
      <div className="space-y-1">
        <p className="font-semibold">algo-coach</p>
        <h1 className="text-title font-semibold">{SIGN_IN_TITLE}</h1>
        <p className="text-meta text-muted-foreground">{LOGIN_INTRO}</p>
      </div>

      {refused !== null && <ErrorLine>{refusal(refused)}</ErrorLine>}

      <Loaded
        of={OF.signIn}
        state={offered}
        blank={NO_SIGN_IN}
        blankWhen={(one) => one.providers.length === 0 && one.dev_login === null}
      >
        {(offered) => (
          <div className="space-y-stack">
            {/* plain links, not the router's: each leaves the app for the API,
                which answers with a redirect */}
            {offered.providers.map((provider) => (
              <Button key={provider} className="w-full" asChild>
                <a href={`/api/auth/${provider}`}>{continueWith(provider)}</a>
              </Button>
            ))}
            {offered.dev_login !== null && (
              <>
                {offered.providers.length > 0 && (
                  // the dev login answers a loopback request alone, so it is
                  // never the act the page asks for
                  <p className="text-center text-meta text-muted-foreground">or</p>
                )}
                <Button variant="outline" className="w-full" asChild>
                  <a href="/api/auth/dev">{devLoginAs(offered.dev_login)}</a>
                </Button>
              </>
            )}
          </div>
        )}
      </Loaded>

      <p className="border-t pt-4 text-meta text-muted-foreground">
        {PRIVACY_NOTE}{' '}
        <Link to={PRIVACY} className="text-foreground underline underline-offset-4">
          {PRIVACY_LINK}
        </Link>
      </p>
    </section>
  )
}
