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
