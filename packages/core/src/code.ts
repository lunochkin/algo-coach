/**
 * Whether a code block wraps its long lines, by the language its fence names.
 * A `text` block or an unnamed one may be a diagram, which wrapping breaks.
 */
export function codeWraps(lang: string | null | undefined): boolean {
  return !!lang && lang !== 'text';
}

export interface CodeLine {
  indent: string;
  text: string;
}

/** A block cut into lines, each split at its indent so a wrap continues under it. */
export function codeLines(code: string): CodeLine[] {
  return code
    .replace(/\s+$/, '')
    .split('\n')
    .map((line) => {
      const indent = /^[ \t]*/.exec(line)![0];
      return { indent, text: line.slice(indent.length) };
    });
}

/** One row a block is drawn in: a line, or the part of one that wrapped (`cont`). */
export interface CodeRow {
  line: number;
  indent: string;
  // where `text` starts in the line's text, so a colouring can be sliced to it
  from: number;
  text: string;
  cont: boolean;
  // the spaces a break dropped after `text`, which a copy puts back
  gap: string;
}

// drawn before a wrapped part and never copied: no Python line can start with it
export const WRAP_MARK = '↪ ';

// a deep indent still leaves this many columns for the code
const ROOM = 12;

// VS Code's break rules, their ASCII part: a break may follow these, or precede those
const AFTER = new Set(' \t})]?|/&.,;');
const BEFORE = new Set('([{+');

// the last place at most `room` in where a break is allowed, else a cut at the edge
function breakAt(text: string, room: number): number {
  for (let j = room; j > room / 2; j--)
    if (text[j] === ' ' || AFTER.has(text[j - 1]) || BEFORE.has(text[j])) return j;
  return room;
}

/** A block's rows at `cols` columns, broken where an editor would break them. */
export function codeRows(code: string, cols: number): CodeRow[] {
  const rows: CodeRow[] = [];
  codeLines(code).forEach(({ indent, text }, line) => {
    let from = 0;
    let rest = text;
    let cont = false;
    for (;;) {
      const room = Math.max(ROOM, cols - indent.length - (cont ? WRAP_MARK.length : 0));
      if (rest.length <= room) break;
      const cut = breakAt(rest, room);
      const head = rest.slice(0, cut).trimEnd();
      const gap = rest.slice(head.length).length - rest.slice(head.length).trimStart().length;
      rows.push({ line, indent, from, text: head, cont, gap: rest.slice(head.length, head.length + gap) });
      from += head.length + gap;
      rest = rest.slice(head.length + gap);
      cont = true;
    }
    rows.push({ line, indent, from, text: rest, cont, gap: '' });
  });
  return rows;
}
