import { describe, expect, it } from 'vitest';

import { studyForm, validDeviceName, validOrigin, validReminderHour } from './settings';

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

describe("the phone's own settings", () => {
  it('checks the address, the device name and the reminder hour', () => {
    expect([validOrigin(' https://example.invalid '), validOrigin('example.invalid')]).toEqual([true, false]);
    expect([validDeviceName('phone-dev'), validDeviceName('my phone')]).toEqual([true, false]);
    expect([validReminderHour(0), validReminderHour(23), validReminderHour(24), validReminderHour(1.5)]).toEqual([
      true,
      true,
      false,
      false,
    ]);
  });
});
