import { lastAt } from './account';
import type { components } from './api/schema';
import {
  CARD_OPTIONAL,
  cardsOffered,
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

/** Every card not in progress, in the API's order. */
export function notInProgress(cards: ListedCard[]): ListedCard[] {
  return cards.filter((card) => !STUDYING.includes(card.status.state));
}

/**
 * A technique's cards as the cards list reads them, in its order: `taught` is
 * what the engine names as teaching the technique or a narrower one.
 */
export function techniqueCards(listed: ListedCard[], taught: { slug: string }[]): ListedCard[] {
  const slugs = new Set(taught.map((one) => one.slug));
  return listed.filter((card) => slugs.has(card.slug));
}

// a family several cards teach is one block under its heading. A family of one
// card joins the unheaded block beside it, since a heading over one row repeats it
export interface CardBlock {
  technique: string | null;
  cards: ListedCard[];
}

/** The cards in blocks, in the API's order, which groups them by family. */
export function cardBlocks(cards: ListedCard[]): CardBlock[] {
  const out: CardBlock[] = [];
  for (const card of cards) {
    const last = out.at(-1);
    const headed = cards.filter((one) => one.family === card.family).length > 1;
    const technique = headed ? card.family : null;
    if (last && last.technique === technique) last.cards.push(card);
    else out.push({ technique, cards: [card] });
  }
  return out;
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

function templateCount(card: ListedCard): string {
  const count = card.templates.length;
  const optional = card.templates.filter((one) => one.optional).length;
  const all = count === 1 ? '1 template' : `${count} templates`;
  return optional === 0 ? all : `${all}, ${optional} optional`;
}

export interface CardRowView {
  title: string;
  // the card's technique where no heading above the row names it
  technique: string | null;
  // at the row's right: when a started card was last active, or the templates
  aside: string;
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
  return {
    title: card.title,
    technique: card.technique === heading ? null : card.technique,
    aside: started ? lastAt(status.last_at, now) : templateCount(card),
    state: started ? cardStateLine(status) : null,
    trigger: started ? null : plain(card.trigger),
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
export const runStartLabel = (starting: boolean) => (starting ? 'Starting…' : 'Start studying this card');
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
