// the knowledge pages' paths, as `pages.md` gives them

export const KNOWLEDGE = '/knowledge'
export const LESSONS = '/knowledge/lessons'
export const CERTIFICATIONS = '/knowledge/certifications'
export const EXAM = '/knowledge/exam'

/** A lesson's page, at one of its sections where `part` names one. */
export function lessonPath(module: string, slug: string, part = ''): string {
  return `${LESSONS}/${module}/${slug}${part ? `#${part}` : ''}`
}
