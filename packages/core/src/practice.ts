import { lastAt } from './account';
import type { components } from './api/schema';
import { described, type EngineClient } from './engine';
import { lessonParts } from './lessontext';
import type { Outcome } from './sittingrun';
import {
  CARD_BRIEF,
  CARD_LOCKED,
  CARD_MET,
  CARD_NOT_STARTED,
  CARD_OPTIONAL,
  CARD_TEMPLATES,
  CARD_TRIGGER,
  cardsDepth,
  cardsOffered,
  cardWaits,
  FORM_NO_CASES,
  FORM_UNCHECKED,
  NO_DIFFICULTY,
  PROCEDURE,
  studyingSince,
  techniquesLine,
} from './words/pages';

// what the board and the cards list say, for every platform

type TechniqueRow = components['schemas']['TechniqueRow'];
type BoardReading = components['schemas']['Board'];
type ListedCard = components['schemas']['ListedCard'];
type Recalled = components['schemas']['Recalled'];
type Picked = components['schemas']['Picked'];
type Template = components['schemas']['Template'];

export interface Stat {
  label: string;
  value: string | number;
}

export function share(solved: number, attempts: number): string {
  return attempts === 0 ? '—' : `${solved}/${attempts}`;
}

/** A technique's counts, each beside its word. An untouched row reads as `never`. */
export function techniqueStats(
  row: Pick<TechniqueRow, 'attempt_count' | 'solved_count' | 'last_attempt_at'>,
  now: number,
): Stat[] {
  if (row.attempt_count === 0) return [{ label: 'attempted', value: 'never' }];
  return [
    { label: row.attempt_count === 1 ? 'attempt' : 'attempts', value: row.attempt_count },
    { label: 'solved', value: share(row.solved_count, row.attempt_count) },
    { label: '', value: lastAt(row.last_attempt_at, now) },
  ];
}

export interface BoardView {
  untouched: TechniqueRow[];
  practised: TechniqueRow[];
  // the attempts no row holds, or null where every attempt has a row
  foot: string | null;
}

export function boardView(board: BoardReading): BoardView {
  const foot = [
    board.ungrouped > 0 && `${board.ungrouped} ${board.ungrouped === 1 ? 'attempt' : 'attempts'} grouped nowhere`,
    board.excluded > 0 && `${board.excluded} on a defective problem`,
  ].filter(Boolean);
  return {
    untouched: board.rows.filter((row) => row.attempt_count === 0),
    practised: board.rows.filter((row) => row.attempt_count > 0),
    foot: foot.length > 0 ? foot.join(' · ') : null,
  };
}

/** What the user has done on one problem, as the line above its statement reads. */
export function problemTried(
  picked: Pick<Picked, 'attempt_count' | 'solved_count' | 'last_attempt_at'>,
  now: number,
): string {
  if (picked.attempt_count === 0) return 'never attempted';
  const attempts = picked.attempt_count === 1 ? '1 attempt' : `${picked.attempt_count} attempts`;
  return `${attempts}, ${share(picked.solved_count, picked.attempt_count)} solved, last ${lastAt(picked.last_attempt_at, now)}`;
}

/**
 * The cards a problem's page offers: those teaching `technique`, the one the
 * pick came from, or else any of the problem's own. A card on a narrower
 * technique teaches its family too, as the cards list groups it.
 */
export function problemCards<C extends Pick<ListedCard, 'technique' | 'family'>>(
  cards: C[],
  techniques: string[],
  technique: string | null,
): C[] {
  const asked = technique === null ? techniques : [technique];
  return cards.filter((card) => asked.includes(card.technique) || asked.includes(card.family));
}

// a graduated card is done, and a lapsed one is offered again: `pages.md`
const STUDYING: ListedCard['status']['state'][] = ['acquiring', 'consolidating'];

/** The cards acquiring or consolidating, the most recently active first. */
export function inProgress(cards: ListedCard[]): ListedCard[] {
  return cards
    .filter((card) => STUDYING.includes(card.status.state))
    .sort((a, b) => (b.status.last_at ?? '').localeCompare(a.status.last_at ?? ''));
}

/**
 * A technique's cards as the cards list reads them, in its order: `taught` is
 * what the engine names as teaching the technique or a narrower one.
 */
export function techniqueCards(listed: ListedCard[], taught: { slug: string }[]): ListedCard[] {
  const slugs = new Set(taught.map((one) => one.slug));
  return listed.filter((card) => slugs.has(card.slug));
}

/** The cards at one depth of the card graph, as the cards list heads them. */
export interface DepthSection {
  depth: number;
  title: string;
  cards: ListedCard[];
}

/** The cards by depth, the roots first, each depth in the API's order. */
export function depthSections(cards: ListedCard[]): DepthSection[] {
  const depths = [...new Set(cards.map((card) => card.depth))].sort((a, b) => a - b);
  return depths.map((depth) => ({
    depth,
    title: cardsDepth(depth),
    cards: cards.filter((card) => card.depth === depth),
  }));
}

/** An edge of the card graph: `from` is required by `to`. One per pair of cards. */
export interface CardEdge {
  from: string;
  to: string;
}

/** Every edge among `cards`, in their order; a requirement on a card not listed draws none. */
export function cardEdges(cards: Pick<ListedCard, 'slug' | 'requires'>[]): CardEdge[] {
  const listed = new Set(cards.map((card) => card.slug));
  const seen = new Set<string>();
  const out: CardEdge[] = [];
  for (const card of cards) {
    for (const one of card.requires ?? []) {
      const key = `${one.card}>${card.slug}`;
      if (listed.has(one.card) && !seen.has(key)) {
        seen.add(key);
        out.push({ from: one.card, to: card.slug });
      }
    }
  }
  return out;
}

/** The phone's line naming a card's required cards, a tick on each met. Null on a root. */
export function cardNeeds(
  card: Pick<ListedCard, 'requires'>,
  cards: Pick<ListedCard, 'slug' | 'title' | 'met'>[],
): string | null {
  const bySlug = new Map(cards.map((one) => [one.slug, one]));
  const required = [...new Set((card.requires ?? []).map((one) => one.card))];
  if (required.length === 0) return null;
  const named = required.map((slug) => {
    const one = bySlug.get(slug);
    return one ? `${one.title}${one.met ? ' ✓' : ''}` : slug;
  });
  return `needs ${named.join(', ')}`;
}

/** Markdown with its marks dropped, for a preview too short to render it. */
export function plain(markdown: string): string {
  return markdown
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

export interface RecallMark {
  templateId: string;
  title: string;
  mark: '-' | '·' | '✗' | '◐' | '✓';
  reading: string;
  // the verdict colour a mark reads in, or null for grey
  tone: 'passed' | 'wrong' | null;
}

/** A recall mark in words, as its hover and its spoken label name it. */
export const recallMarkLabel = (one: Pick<RecallMark, 'title' | 'reading'>) => `${one.title}: ${one.reading}`;

function recallMark(cases: number, last: Recalled | undefined): Pick<RecallMark, 'mark' | 'reading' | 'tone'> {
  if (cases === 0) return { mark: '-', reading: 'read, not recalled', tone: null };
  if (!last?.last_at) return { mark: '·', reading: 'never recalled', tone: null };
  if (!last.verified) return { mark: '✗', reading: 'failed', tone: 'wrong' };
  return last.hints.length > 0
    ? { mark: '◐', reading: 'passed with hints', tone: null }
    : { mark: '✓', reading: 'recalled clean', tone: 'passed' };
}

/** One mark per template, in the card's order: the last recall of each form. */
export function recallMarks(card: ListedCard): RecallMark[] {
  const recalled = new Map(card.status.recall.map((one) => [one.template_id, one]));
  return card.templates.map((template) => ({
    templateId: template.id,
    title: template.title,
    ...recallMark(template.cases?.length ?? 0, recalled.get(template.id)),
  }));
}

/** A started card's line: when it began, the ladder, and the forms no rung covers. */
export function cardStateLine(status: ListedCard['status']): string {
  const started = status.started_at ? new Date(status.started_at).toLocaleDateString() : '';
  const gaps =
    status.gaps === 0 ? '' : ` · ${status.gaps === 1 ? '1 form uncovered' : `${status.gaps} forms uncovered`}`;
  return `started ${started} · ladder ${status.solved}/${status.rungs}, required ${status.required_solved}/${status.required}${gaps}`;
}

export interface CardRowView {
  title: string;
  // the card's technique where no heading above the row names it
  technique: string | null;
  // at the row's right: locked, met, when a started card was last active, or
  // not started
  aside: string;
  // a locked card's line, in the trigger's place: the required cards not met
  waits: string | null;
  // a started card reads its progress; any other reads the trigger it is picked by
  state: string | null;
  trigger: string | null;
  progress: { solved: number; rungs: number } | null;
  recall: RecallMark[];
}

/** A card's row under `heading`, the technique its panel names, if any. */
export function cardRow(card: ListedCard, heading: string | null, now: number): CardRowView {
  const { status } = card;
  const started = Boolean(status.started_at);
  const waiting = card.waiting ?? [];
  const locked = waiting.length > 0;
  return {
    title: card.title,
    technique: card.technique === heading ? null : card.technique,
    aside: locked ? CARD_LOCKED : card.met ? CARD_MET : started ? lastAt(status.last_at, now) : CARD_NOT_STARTED,
    waits: locked ? cardWaits(waiting.map((one) => one.title)) : null,
    state: started ? cardStateLine(status) : null,
    trigger: started || locked ? null : plain(card.trigger),
    progress: started ? { solved: status.solved, rungs: status.rungs } : null,
    recall: recallMarks(card),
  };
}

/** A template's last recall. A hinted pass is not a pass, so the hints read beside it. */
export function recallLine(one: Recalled | undefined, now: number): string {
  if (one === undefined || one.last_at === null) return 'Never recalled';
  const n = one.hints.length;
  const hints = n === 0 ? 'no hint taken' : n === 1 ? '1 hint' : `${n} hints`;
  return `Recalled ${lastAt(one.last_at, now)} · ${one.verified ? 'passed' : 'failed'} · ${hints}`;
}

/** How a card shows one template, on both clients, before the form is revealed. */
export interface TemplateView {
  recallable: boolean; // a template no case checks is read and never recalled: `content.md`
  badges: string[];
  status: string; // how its recall has gone, or why it has none
  unchecked: string | null; // said where the recall press would sit
  reveal: string;
}

export function templateView(
  template: Pick<Template, 'cases' | 'optional' | 'kind' | 'code'>,
  recalled: Recalled | undefined,
  now: number,
): TemplateView {
  const recallable = (template.cases ?? []).length > 0;
  return {
    recallable,
    badges: [template.optional ? CARD_OPTIONAL : null, template.kind === 'procedure' ? PROCEDURE : null].filter(
      (one): one is string => one !== null,
    ),
    status: recallable ? recallLine(recalled, now) : FORM_NO_CASES,
    unchecked: recallable ? null : FORM_UNCHECKED,
    reveal: revealLabel(template.code),
  };
}

/** A problem's facts, in the one line above its statement or its retired record. */
export interface ProblemFacts<C> {
  difficulty: string;
  techniques: string;
  tried: string;
  cards: C[];
  cardsLabel: string | null;
}

export function problemFacts<C extends Pick<ListedCard, 'technique' | 'family'>>(
  picked: Pick<Picked, 'difficulty' | 'techniques' | 'attempt_count' | 'solved_count' | 'last_attempt_at'>,
  cards: C[],
  technique: string | null,
  now: number,
): ProblemFacts<C> {
  const offered = problemCards(cards, picked.techniques, technique);
  return {
    difficulty: picked.difficulty ?? NO_DIFFICULTY,
    techniques: techniquesLine(picked.techniques),
    tried: problemTried(picked, now),
    cards: offered,
    cardsLabel: offered.length ? cardsOffered(offered.length) : null,
  };
}

/** The press covering a form: its length, and nothing of the form. */
export function revealLabel(code: string): string {
  const lines = code.trimEnd().split('\n').length;
  return `Reveal the form · ${lines === 1 ? '1 line' : `${lines} lines`}`;
}

/** Why a read of `what` failed. With no connection, the device holds no copy to show instead. */
export function readFailure(what: string, error: string): string {
  if (/network request failed|failed to fetch|timed? ?out|offline/i.test(error)) {
    return `No connection, and this device holds no copy of ${what}.`;
  }
  return `${what[0].toUpperCase()}${what.slice(1)} did not load: ${error}`;
}

// a page's reading before its content, the same on both clients
export const loadingLine = (what: string) => `Loading ${what}…`;
export const RETRY = 'Retry';

type Studied = components['schemas']['Studied'];

export interface RungRow {
  problemId: string;
  title: string;
  difficulty: string | null;
  // the templates the rung covers, by title, or null where it covers none
  covers: string | null;
  need: 'required' | 'optional';
  // whether the rung is solved since the run began, or null where no run is open
  solved: boolean | null;
}

export interface LadderView {
  // the rungs, beside the section's heading
  count: number;
  // how many are solved, where a run is open
  aside: string | null;
  rows: RungRow[];
  // a core template no problem covers yet: `content.md`, Cards
  gaps: string[];
}

/** A card's ladder: each rung, what it covers, and the gaps. Progress reads once a run is open. */
export function ladderView(studied: Studied): LadderView {
  const titles = new Map(studied.card.templates.map((one) => [one.id, one.title]));
  const solved = studied.rungs.filter((one) => one.solved).length;
  const n = studied.rungs.length;
  return {
    count: n,
    aside: studied.run ? `${solved} of ${n} solved` : null,
    rows: studied.rungs.map((rung) => ({
      problemId: rung.problem.id,
      title: rung.problem.title,
      difficulty: rung.problem.difficulty ?? null,
      covers: rung.templates.length ? `covers ${rung.templates.map((id) => titles.get(id) ?? id).join(', ')}` : null,
      need: rung.required ? 'required' : 'optional',
      solved: studied.run ? rung.solved : null,
    })),
    gaps: studied.gaps.map((gap) => `No problem covers ${gap.title} yet.`),
  };
}

export const LADDER_TITLE = 'Ladder';
export const LADDER_GAP = 'gap';
export const PROBES_TITLE = 'Probes';
export const PROBES_ASIDE = 'drawn at the start, never from the ladder';
export const probeState = (attempted: boolean) => (attempted ? 'attempted' : 'not attempted');

// the press opening a card's run: the ladder counts from it, so a problem
// solved before it counts toward nothing
export const RUN_START_NOTE =
  'The ladder is measured from the start, so a problem solved before it counts toward nothing.';
export const runStartLabel = (starting: boolean, locked = false) =>
  locked ? 'Locked' : starting ? 'Starting…' : 'Start studying this card';

/**
 * The note a locked card's press reads in place of the start note: the
 * required cards not yet met, and how one is met. Null where the card starts.
 */
export function runLock(waiting: Studied['waiting']): string | null {
  if (waiting.length === 0) return null;
  const names = waiting.map((one) => one.title);
  const listed = names.length === 1 ? names[0] : `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`;
  return `Waits on ${listed}. A card is met by solving its ladder, or one of its probes.`;
}
export const runStartRefused = (error: string) => `The card did not start: ${error}`;

/** What a run has reached on a card: the rungs solved, the forms recalled, the probes drawn and the rung next. */
export interface CardProgress {
  solved: number;
  rungs: number;
  recalled: number;
  forms: number;
  probes: number;
  // the first unsolved required rung, else the first unsolved, in the ladder's order
  next: { problemId: string; title: string } | null;
  // a recall is offered where some template carries cases to check it
  recallable: boolean;
}

export function cardProgress(studied: Studied): CardProgress {
  const open = studied.rungs.filter((one) => !one.solved);
  const next = open.find((one) => one.required) ?? open[0];
  return {
    solved: studied.rungs.length - open.length,
    rungs: studied.rungs.length,
    recalled: studied.recall.filter((one) => one.last_at !== null).length,
    forms: studied.card.templates.length,
    probes: studied.probes.length,
    next: next ? { problemId: next.problem.id, title: next.problem.title } : null,
    recallable: studied.card.templates.some((one) => (one.cases ?? []).length > 0),
  };
}

/** The line under a card's title: its technique, and since when a run studies it. */
export function cardNote(studied: Studied, now: number): string {
  const run = studied.run;
  return [studied.card.technique, run && studyingSince(lastAt(run.started_at, now))].filter(Boolean).join(' · ');
}

/**
 * A card's brief cut at its `##` headings, as a lesson is, so each heading is
 * a section of the card's page rather than a heading inside one. Text before
 * the first heading reads under the brief's own title.
 */
export function briefParts(brief: string): { id: string; title: string; text: string }[] {
  return lessonParts(brief).map((part) =>
    part.title === null
      ? { id: 'brief', title: CARD_BRIEF, text: part.text }
      : // prefixed: a brief heading named like the ladder must not take its id
        { id: `brief-${part.anchor}`, title: part.title, text: part.text },
  );
}

/** A card's sections, as both clients' section bars name them. Probes read only once a run drew some. */
export function cardSections(
  studied: (Pick<Studied, 'probes'> & { card: Pick<Studied['card'], 'brief'> }) | null | undefined,
): { id: string; label: string }[] {
  if (!studied) return [];
  return [
    { id: 'trigger', label: CARD_TRIGGER },
    ...briefParts(studied.card.brief).map((part) => ({ id: part.id, label: part.title })),
    { id: 'ladder', label: LADDER_TITLE },
    ...(studied.probes.length > 0 ? [{ id: 'probes', label: PROBES_TITLE }] : []),
    { id: 'templates', label: CARD_TEMPLATES },
  ];
}

/** Opens a run on a card, which draws its probes. A refusal is named rather than read as a start. */
export async function startCardRun(client: EngineClient, slug: string): Promise<Outcome<null>> {
  try {
    const { error } = await client.POST('/api/cards/{slug}/runs', { params: { path: { slug } } });
    return error === undefined ? { ok: true, value: null } : { ok: false, refused: described(error) };
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}
