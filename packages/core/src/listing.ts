import type { components } from './api/schema';

// the problem listing, for every platform: `pages.md`, Sections. The whole
// listing is read, since the tags count every problem the corpus carries, and
// a page is a slice of what the two filters left

type Listed = components['schemas']['Listed'];

export const PER_PAGE = 20;

// the three a problem carries, in the order a solver reads them rather than
// the order they count in
export const DIFFICULTIES = ['easy', 'medium', 'hard'] as const;

export interface ListingFilter {
  techniques: string[];
  difficulties: string[];
  page: number;
}

export interface Chip {
  name: string;
  count: number;
  on: boolean;
}

export interface ListingView {
  difficulties: Chip[];
  tags: Chip[];
  shown: number;
  filtered: boolean;
  page: number;
  pages: number;
  rows: Listed[];
  // the one tag the listing is filtered to: a pick from it drills that technique
  drilled: string | null;
}

// a problem shows where it carries any tag picked and sits at any difficulty
// asked for: a second pick in one filter widens, and the two filters narrow
const carries = (one: Listed, picked: string[]) =>
  picked.length === 0 || picked.some((technique) => one.techniques.includes(technique));
const asked = (one: Listed, difficulties: string[]) =>
  difficulties.length === 0 || (one.difficulty !== null && difficulties.includes(one.difficulty));

function held(listed: Listed[]): Map<string, number> {
  const counted = new Map<string, number>();
  for (const one of listed)
    for (const technique of one.techniques) counted.set(technique, (counted.get(technique) ?? 0) + 1);
  return counted;
}

/**
 * The listing under `filter`. Each chip counts what pressing it would leave,
 * and the tags keep the whole listing's order so no chip moves as a count does.
 */
export function listingView(listed: Listed[], filter: ListingFilter): ListingView {
  const byDifficulty = listed.filter((one) => asked(one, filter.difficulties));
  const byTag = listed.filter((one) => carries(one, filter.techniques));
  const shown = byDifficulty.filter((one) => carries(one, filter.techniques));
  const pages = Math.max(1, Math.ceil(shown.length / PER_PAGE));
  const page = Math.min(Math.max(1, filter.page), pages);
  const counted = held(byDifficulty);
  return {
    difficulties: DIFFICULTIES.map((name) => ({
      name,
      count: byTag.filter((one) => one.difficulty === name).length,
      on: filter.difficulties.includes(name),
    })),
    tags: [...held(listed)]
      .sort(([one, a], [other, b]) => b - a || one.localeCompare(other))
      .map(([name]) => ({ name, count: counted.get(name) ?? 0, on: filter.techniques.includes(name) })),
    shown: shown.length,
    filtered: filter.techniques.length > 0 || filter.difficulties.length > 0,
    page,
    pages,
    rows: shown.slice((page - 1) * PER_PAGE, page * PER_PAGE),
    drilled: filter.techniques.length === 1 ? filter.techniques[0] : null,
  };
}

/** A chip pressed: on where it was off, off where it was on. A filter returns the listing to its first page. */
export function toggled(filter: ListingFilter, kind: 'techniques' | 'difficulties', name: string): ListingFilter {
  const now = filter[kind];
  const next = now.includes(name) ? now.filter((one) => one !== name) : [...now, name];
  return { ...filter, [kind]: next, page: 1 };
}

export const NO_FILTER: ListingFilter = { techniques: [], difficulties: [], page: 1 };

export const PROBLEMS_TITLE = 'Problems';
export const PROBLEMS_NOTE =
  'Every problem the engine has written. A difficulty and a tag narrow the list, and a problem shows where it matches both.';
export const PROBLEMS_NONE = 'No problem is served yet.';
export const PROBLEMS_NONE_MATCH = 'No problem carries a tag you picked at the difficulty you asked for.';
export const listingHeading = (filtered: boolean) => (filtered ? 'Matching your filters' : 'Every problem');
export function clearFilters(filter: ListingFilter): string {
  const n = filter.techniques.length + filter.difficulties.length;
  return n === 1 ? 'Clear the filter' : `Clear all ${n} filters`;
}
export const pageOf = (page: number, pages: number) => `Page ${page} of ${pages}`;
export const PAGE_PREVIOUS = 'Previous';
export const PAGE_NEXT = 'Next';
