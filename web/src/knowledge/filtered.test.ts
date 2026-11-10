import { describe, expect, it } from 'vitest'

import { loadSnapshot } from '@algo-coach/core'

import { filteredQuery, filteredScope } from '@/knowledge/filtered'

const catalog = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'python',
      definition: {
        title: 'Python',
        pass_ratio: 1,
        kinds: ['concept', 'output'],
        topic: [{ slug: 'core', tier: 1, title: 'Core', subs: ['names', 'types'] }],
      },
      questions: [],
    },
  ],
} as never)

const read = (url: string) => filteredScope(new URL(url, 'http://x').searchParams, catalog)

describe("a filtered queue's URL", () => {
  it('carries every choice the sheet made, and reads them back', () => {
    const scope = {
      course: 'python',
      topic: 'core',
      sub: 'names',
      level: 1,
      kind: 'output',
      due: true,
    }
    expect(read(filteredQuery(scope))).toEqual(scope)
  })

  it('names the module alone where the sheet narrowed nothing', () => {
    expect(filteredQuery({ course: 'python' })).toBe('/knowledge/queue?mode=filtered&module=python')
  })

  it('keeps the module where the topic is gone, as a focus degrades', () => {
    expect(read('/knowledge/queue?mode=filtered&module=python&topic=gone&sub=names')).toMatchObject(
      {
        course: 'python',
        topic: null,
        sub: null,
      },
    )
  })

  it('keeps the topic where the subtopic is gone', () => {
    expect(read('/knowledge/queue?mode=filtered&module=python&topic=core&sub=gone')).toMatchObject({
      topic: 'core',
      sub: null,
    })
  })

  it('drops a level or a kind the module does not hold', () => {
    expect(read('/knowledge/queue?mode=filtered&module=python&level=9&kind=debug')).toMatchObject({
      level: null,
      kind: null,
    })
  })

  it('reads no queue where the module is not one the user reads', () => {
    expect(read('/knowledge/queue?mode=filtered&module=rust')).toBeNull()
  })
})
