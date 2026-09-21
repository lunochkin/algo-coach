import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

// relative: the page and the API share one origin. Every request says JSON,
// since the API refuses a write that does not, and a write with no body would
// otherwise send no content type
export const api = createClient<paths>({ headers: { 'Content-Type': 'application/json' } })

// the login page needs no session, so it is the one page a refusal leaves be
export const LOGIN = '/login'
// sends no request, so a person with no account reads it; Google's consent
// screen links here
export const PRIVACY = '/privacy'

// a request with no session sends the browser to the login. A full load rather
// than the router's: the login's own links leave the app for the provider
api.use({
  onResponse({ response }) {
    if (response.status === 401 && window.location.pathname !== LOGIN) {
      window.location.assign(LOGIN)
    }
  },
})

export type Board = components['schemas']['Board']
export type TechniqueRow = components['schemas']['TechniqueRow']
export type Card = components['schemas']['Card']
export type Studied = components['schemas']['Studied']
export type Rung = components['schemas']['Rung']
export type Recalled = components['schemas']['Recalled']
export type Named = components['schemas']['Named']
export type Gap = components['schemas']['Gap']
export type Template = components['schemas']['Template']
export type Submitted = components['schemas']['Submitted']
export type Sitting = components['schemas']['Sitting']
export type Attempt = components['schemas']['Attempt']
export type FailureMode = components['schemas']['FailureMode']
export type Failure = components['schemas']['Failure']
export type CaseResult = components['schemas']['CaseResult']
export type Hint = components['schemas']['Hint']
export type RecallAttempt = components['schemas']['RecallAttempt']
export type Candidate = components['schemas']['Candidate']
export type Listed = components['schemas']['Listed']
export type Picked = components['schemas']['Picked']
export type Provider = components['schemas']['Provider']
export type Me = components['schemas']['Me']

export function candidates(technique: string, signal: AbortSignal) {
  return api.GET('/api/techniques/{technique}/candidates', {
    params: { path: { technique } },
    signal,
  })
}
