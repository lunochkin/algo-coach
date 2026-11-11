export type SettingName = 'new_per_day' | 'exam_size';

/** A study setting as set: the latest of each name stands on every device. */
export interface SettingRecord {
  t: string;
  name: SettingName;
  n: number;
}

export const SETTING_DEFAULT: Record<SettingName, number> = { new_per_day: 10, exam_size: 40 };

// the engine refuses a value outside these: `knowledge.md`, The records
export const SETTING_RANGE: Record<SettingName, [number, number]> = { new_per_day: [0, 200], exam_size: [1, 500] };

export function validSetting(name: SettingName, n: number): boolean {
  const [low, high] = SETTING_RANGE[name];
  return Number.isInteger(n) && n >= low && n <= high;
}

/** The value the latest record of `name` set, file order breaking a tie; the default where none did. */
export function setting(records: readonly SettingRecord[], name: SettingName): number {
  let latest: SettingRecord | null = null;
  for (const r of records) if (r.name === name && (!latest || Date.parse(r.t) >= Date.parse(latest.t))) latest = r;
  return latest ? latest.n : SETTING_DEFAULT[name];
}

// the Study settings, in the phone's order: `pages.md`, Sections
export const STUDY_SETTINGS: readonly SettingName[] = ['new_per_day', 'exam_size'];

export interface StudyForm {
  values: Record<SettingName, number>;
  ok: Record<SettingName, boolean>;
  valid: boolean;
  changed: SettingName[]; // the ones a save writes
}

/** The Study settings as typed, read against the stored values. */
export function studyForm(typed: Record<SettingName, string>, stored: Record<SettingName, number>): StudyForm {
  const values = { new_per_day: Number(typed.new_per_day), exam_size: Number(typed.exam_size) };
  const ok = {
    new_per_day: validSetting('new_per_day', values.new_per_day),
    exam_size: validSetting('exam_size', values.exam_size),
  };
  return {
    values,
    ok,
    valid: STUDY_SETTINGS.every((name) => ok[name]),
    changed: STUDY_SETTINGS.filter((name) => values[name] !== stored[name]),
  };
}

// the phone's own settings, each checked where its rule is worded: `pages.md`, The two clients
export const validOrigin = (origin: string) => /^https?:\/\/[^\s/]+$/.test(origin.trim());
export const validDeviceName = (name: string) => /^[A-Za-z0-9_-]+$/.test(name);
export const validReminderHour = (hour: number) => Number.isInteger(hour) && hour >= 0 && hour <= 23;
