const KEY = 'algo-coach:clock'

// whether a sitting's clock starts by itself when the statement is served.
// Off until the user first starts a clock: `flows.md` has the clock started by
// choice
export function autoStarts(): boolean {
  try {
    return localStorage.getItem(KEY) === 'on'
  } catch {
    return false
  }
}

// set by the user's own press alone: a pause the hidden page took says
// nothing about how the user means to practise
export function pressed(started: boolean): void {
  try {
    localStorage.setItem(KEY, started ? 'on' : 'off')
  } catch {
    // a browser refusing storage costs the preference, not the clock
  }
}
