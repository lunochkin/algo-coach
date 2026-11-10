import { describe, expect, it } from 'vitest';

import { askSubmit, detailsToggle, examReviewNext, lessonNote, lessonRowLine } from '../index';

describe('queue words', () => {
  it('names the answer press by whether an exam runs and ends', () => {
    expect([askSubmit(false, true), askSubmit(true, false), askSubmit(true, true)]).toEqual([
      'Submit',
      'Next',
      'Submit and finish',
    ]);
  });

  it('reads the details toggle and the review press by their state', () => {
    expect([detailsToggle(false), detailsToggle(true)]).toEqual(['Details', 'Hide details']);
    expect([examReviewNext(false), examReviewNext(true)]).toEqual(['Next missed', 'Back to results']);
  });

  it('drops the minutes of a lesson whose text is not held', () => {
    expect(lessonRowLine(0, 'Basics')).toBe('Basics');
    expect(lessonRowLine(7, 'Basics')).toBe('~7 min · Basics');
    expect(lessonNote('Python', null, false)).toBe('Python');
    expect(lessonNote('Python', 7, true)).toBe('Python · ~7 min · read');
  });
});
