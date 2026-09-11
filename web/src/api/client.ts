import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

// relative: the page and the API share one origin
export const api = createClient<paths>()

export type Board = components['schemas']['Board']
export type Card = components['schemas']['Card']
export type Template = components['schemas']['Template']
export type Submitted = components['schemas']['Submitted']
export type Sitting = components['schemas']['Sitting']
export type Failure = components['schemas']['Failure']
export type Candidate = components['schemas']['Candidate']

export function candidates(technique: string, signal: AbortSignal) {
  return api.GET('/api/techniques/{technique}/candidates', {
    params: { path: { technique } },
    signal,
  })
}
