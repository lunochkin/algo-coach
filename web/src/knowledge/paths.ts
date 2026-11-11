// the knowledge pages' paths, as `pages.md` gives them

export const KNOWLEDGE = '/knowledge'
export const LESSONS = '/knowledge/lessons'
export const CERTIFICATIONS = '/knowledge/certifications'
export const EXAM = '/knowledge/exam'

/** A lesson's page, at one of its sections where `part` names one. */
export function lessonPath(module: string, slug: string, part = ''): string {
  return `${LESSONS}/${module}/${slug}${part ? `#${part}` : ''}`
}

/** A module's page; `from` names the page its way back returns to, as `?from=` does on a problem. */
export function modulePath(module: string, from?: 'board'): string {
  return `${KNOWLEDGE}/modules/${module}${from ? `?from=${from}` : ''}`
}
