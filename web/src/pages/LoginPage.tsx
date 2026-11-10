import { Link, useSearchParams } from "react-router";

import {
  continueWith,
  devLoginAs,
  LOGIN_INTRO,
  NO_SIGN_IN,
  refusal,
} from "@algo-coach/core";

import { api, PRIVACY } from "@/api/client";
import { useLoaded } from "@/api/useLoaded";
import { Loaded } from "@/components/Loaded";
import { Button } from "@/components/ui/button";

export function LoginPage() {
  const offered = useLoaded(
    (signal) => api.GET("/api/sign-in", { signal }),
    "sign-in",
  );
  const [search] = useSearchParams();
  const refused = search.get("refused");

  return (
    <section className="mx-auto max-w-form space-y-section py-16">
      <div className="space-y-1">
        <p className="font-semibold">algo-coach</p>
        <h1 className="text-title font-semibold">Sign in</h1>
        <p className="text-meta text-muted-foreground">{LOGIN_INTRO}</p>
      </div>

      {refused !== null && (
        <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-meta text-destructive">
          {refusal(refused)}
        </p>
      )}

      <Loaded
        of="the sign-in"
        state={offered}
        blank={NO_SIGN_IN}
        blankWhen={(one) =>
          one.providers.length === 0 && one.dev_login === null
        }
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
                  <p className="text-center text-meta text-muted-foreground">
                    or
                  </p>
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
        The app stores what you attempt and what a model says about it.{" "}
        <Link
          to={PRIVACY}
          className="text-foreground underline underline-offset-4"
        >
          Privacy policy
        </Link>
      </p>
    </section>
  );
}
