// the knowledge pages' paths, as `pages.md` gives them

export const KNOWLEDGE = '/knowledge'
export const LESSONS = '/knowledge/lessons'

/** A lesson's page, at one of its sections where `part` names one. `back` is the page to return to. */
export function lessonPath(module: string, slug: string, part = '', back?: string): string {
  const query = back ? `?${new URLSearchParams({ back })}` : ''
  return `${LESSONS}/${module}/${slug}${query}${part ? `#${part}` : ''}`
}
