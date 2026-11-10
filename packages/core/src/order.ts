// imports nothing: the web's pages import it before the web joins the workspace

/** The user's order of the modules, by slug, first to last: the latest stands on every device. */
export interface OrderRecord {
  t: string;
  courses: string[];
}

/** The module order the latest record set, file order breaking a tie; none where no device set one. */
export function moduleOrder(orders: readonly OrderRecord[]): string[] {
  let latest: OrderRecord | null = null;
  for (const r of orders) if (!latest || Date.parse(r.t) >= Date.parse(latest.t)) latest = r;
  return latest?.courses ?? [];
}

/** The slugs with the one at `from` moved to `to`. */
export function moved(slugs: readonly string[], from: number, to: number): string[] {
  const out = [...slugs];
  const [one] = out.splice(from, 1);
  if (one !== undefined) out.splice(to, 0, one);
  return out;
}

/** Sort by a saved slug order; slugs not in it keep their original relative order, after the known ones. */
export function bySavedOrder<T>(items: readonly T[], slug: (t: T) => string, order: readonly string[]): T[] {
  const rank = new Map(order.map((s, i) => [s, i]));
  return items
    .map((t, i) => ({ t, i, r: rank.get(slug(t)) ?? order.length + i }))
    .sort((a, b) => a.r - b.r)
    .map((x) => x.t);
}
