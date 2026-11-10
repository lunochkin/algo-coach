import { lastAt } from './account';
import type { components } from './api/schema';

// what the board and the cards list say, for every platform

type TechniqueRow = components['schemas']['TechniqueRow'];
type BoardReading = components['schemas']['Board'];
type ListedCard = components['schemas']['ListedCard'];
type Recalled = components['schemas']['Recalled'];

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
  const gaps = status.gaps === 0 ? '' : ` · ${status.gaps === 1 ? '1 form uncovered' : `${status.gaps} forms uncovered`}`;
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

/** The press covering a form: its length, and nothing of the form. */
export function revealLabel(code: string): string {
  const lines = code.trimEnd().split('\n').length;
  return `Reveal the form · ${lines === 1 ? '1 line' : `${lines} lines`}`;
}

/** Why a read from the engine failed, where the device holds no copy of `what`. */
export function readFailure(what: string, error: string): string {
  if (/network request failed|failed to fetch|timed? ?out|offline/i.test(error)) {
    return `No connection. ${what[0].toUpperCase()}${what.slice(1)} are read from the engine, and this device holds no copy.`;
  }
  return `${what[0].toUpperCase()}${what.slice(1)} did not load: ${error}`;
}
