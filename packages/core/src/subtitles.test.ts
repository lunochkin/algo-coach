import { describe, expect, it } from 'vitest';

import { loadSnapshot, subTitle, topicTitle } from './index';

const cat = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'c',
      definition: {
        title: 'C',
        pass_ratio: 1,
        kinds: ['k'],
        topic: [
          { slug: 't', tier: 1, title: 'T', subs: ['types', 'flow'], sub_titles: { types: 'Mutability and identity' } },
        ],
      },
      questions: [],
    },
  ],
} as never);

describe('a subtopic title', () => {
  it('names a subtopic its module titles', () => {
    expect(subTitle(cat.courses[0], 'types')).toBe('Mutability and identity');
  });
  it('falls back to the slug where the module gives none', () => {
    expect(subTitle(cat.courses[0], 'flow')).toBe('flow');
  });
});

describe('a topic title', () => {
  it("names a topic by its module's title for it", () => {
    expect(topicTitle(cat.courses[0], 't')).toBe('T');
  });
  it('falls back to the slug for a topic the module does not hold', () => {
    expect(topicTitle(cat.courses[0], 'nowhere')).toBe('nowhere');
  });
});
