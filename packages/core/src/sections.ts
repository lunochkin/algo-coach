// a long page's sections, on both clients: nothing is closed until the reader
// closes it, and a jump opens the section it lands on. `pages.md`, A page's areas

/** The closed sections once the reader presses one section's heading. */
export function sectionToggled(closed: readonly string[], id: string): string[] {
  return closed.includes(id) ? closed.filter((one) => one !== id) : [...closed, id];
}

/** The closed sections once a jump lands on one, which it opens. */
export function sectionOpened(closed: readonly string[], id: string): string[] {
  return closed.filter((one) => one !== id);
}
