/** How a markdown table reads: a grid, or one block per row. */
export type TableShape = 'grid' | 'rows';

// the space a grid sets between two columns, in characters
export const TABLE_GAP = 2;

/**
 * A grid where every column holds its longest cell within `cols` characters
 * of prose, and blocks otherwise: `pages.md`, The design system.
 */
export function tableShape(header: string[], rows: string[][], cols: number): TableShape {
  const widths = header.map((h, i) => Math.max(h.trim().length, ...rows.map((r) => (r[i] ?? '').trim().length)));
  const width = widths.reduce((a, b) => a + b, 0) + TABLE_GAP * (widths.length - 1);
  return width <= cols ? 'grid' : 'rows';
}
