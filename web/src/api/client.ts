import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

// relative: the page and the API share one origin
export const api = createClient<paths>()

export type Board = components['schemas']['Board']
export type TechniqueRow = components['schemas']['TechniqueRow']
