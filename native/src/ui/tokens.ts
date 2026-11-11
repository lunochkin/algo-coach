// the colours the phone's theme holds no role for: a verdict's outcomes, and
// a group or a certification read as done or open. The theme is the device's
// own Material palette, so these are the phone's one place for them, each
// outcome apart as on the web: `pages.md`, The design system. A running clock
// carries a token of its own, since it is not a passed case
export const TONES = {
  light: { passed: '#2e7d32', timeout: '#a15c00', crashed: '#7b1fa2', running: '#2e7d32' },
  dark: { passed: '#81c784', timeout: '#ffb74d', crashed: '#ce93d8', running: '#81c784' },
} as const;

export const palette = (dark: boolean) => (dark ? TONES.dark : TONES.light);

// the spacing steps, keyed as the web's 4px steps are: `space[2]` is the
// web's `gap-2`. `gutter` is a screen's and a row's edge, `stack` the gap
// between a screen's blocks
export const space = {
  0: 0,
  px: 1,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  gutter: 16,
  stack: 12,
} as const;

// the type sizes the theme's variants leave unset, named by the web's roles.
// Text reads a theme variant first; a size is set only where none fits
export const textSize = {
  title: 24,
  heading: 18,
  meta: 14,
  body: 16,
  micro: 10,
  code: 14,
  codeInline: 13,
} as const;

export const font = { mono: 'monospace' } as const;

// every radius derives from the theme's one base, as the web's from `--radius`
export const radius = (theme: { roundness: number }) => {
  const r = theme.roundness;
  return { xs: r / 2, sm: r, md: r * 1.5, lg: r * 2, xl: r * 3, full: 999 } as const;
};
