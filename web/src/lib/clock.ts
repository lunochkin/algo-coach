import { CLOCK_PREFERENCE_KEY, clockStartsItself, preferenceAfter } from '@algo-coach/core'

// the clock preference in this browser: core decides what a press sets
export function autoStarts(): boolean {
  try {
    return clockStartsItself(localStorage.getItem(CLOCK_PREFERENCE_KEY))
  } catch {
    return false
  }
}

export function pressed(to: 'start' | 'pause' | 'resume'): void {
  try {
    localStorage.setItem(CLOCK_PREFERENCE_KEY, preferenceAfter(to))
  } catch {
    // a browser refusing storage costs the preference, not the clock
  }
}
