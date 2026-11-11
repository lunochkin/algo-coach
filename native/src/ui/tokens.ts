// the colours the phone's theme holds no role for: a verdict's outcomes, and
// a group or a certification read as done or open. The theme is the device's
// own Material palette, so these are the phone's one place for them, each
// outcome apart as on the web: `pages.md`, The design system
export const TONES = {
  light: { passed: '#2e7d32', timeout: '#a15c00', crashed: '#7b1fa2' },
  dark: { passed: '#81c784', timeout: '#ffb74d', crashed: '#ce93d8' },
} as const;

export const palette = (dark: boolean) => (dark ? TONES.dark : TONES.light);
