/** Sort by a saved slug order; slugs not in it keep their original relative order, after the known ones. */
export function bySavedOrder<T>(items: readonly T[], slug: (t: T) => string, order: readonly string[]): T[] {
  const rank = new Map(order.map((s, i) => [s, i]));
  return items
    .map((t, i) => ({ t, i, r: rank.get(slug(t)) ?? order.length + i }))
    .sort((a, b) => a.r - b.r)
    .map((x) => x.t);
}

/** Move the item with the given slug to the front, keeping the rest in order. */
export function withFirst<T>(items: readonly T[], slug: (t: T) => string, first: string): T[] {
  return [...items.filter((t) => slug(t) === first), ...items.filter((t) => slug(t) !== first)];
}
