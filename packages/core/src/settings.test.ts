import { describe, expect, it } from 'vitest';

import { studyForm } from './settings';

const stored = { new_per_day: 10, exam_size: 40 };

describe('studyForm', () => {
  it('names only the settings whose typed value moved', () => {
    const form = studyForm({ new_per_day: '10', exam_size: '25' }, stored);
    expect([form.valid, form.changed, form.values.exam_size]).toEqual([true, ['exam_size'], 25]);
  });

  it('is invalid where one value is outside its range or not whole', () => {
    expect(studyForm({ new_per_day: '201', exam_size: '40' }, stored).ok).toEqual({
      new_per_day: false,
      exam_size: true,
    });
    expect(studyForm({ new_per_day: '10', exam_size: '2.5' }, stored).valid).toBe(false);
  });
});
