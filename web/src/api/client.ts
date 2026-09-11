import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

// relative: the page and the API share one origin. Every request says JSON,
// since the API refuses a write that does not, and a write with no body would
// otherwise send no content type
export const api = createClient<paths>({ headers: { 'Content-Type': 'application/json' } })

export type Board = components['schemas']['Board']
export type Card = components['schemas']['Card']
export type Template = components['schemas']['Template']
export type Submitted = components['schemas']['Submitted']
export type Sitting = components['schemas']['Sitting']
export type Attempt = components['schemas']['Attempt']
export type Failure = components['schemas']['Failure']
export type Candidate = components['schemas']['Candidate']

export function candidates(technique: string, signal: AbortSignal) {
  return api.GET('/api/techniques/{technique}/candidates', {
    params: { path: { technique } },
    signal,
  })
}
