// a statement's `$…$` math, read as Unicode text: the web typesets it with
// KaTeX, which on a phone needs a WebView per formula. An unknown command is
// left as its source, so a reader still sees what was written

const SYMBOLS: Record<string, string> = {
  le: '≤',
  leq: '≤',
  ge: '≥',
  geq: '≥',
  ne: '≠',
  neq: '≠',
  lt: '<',
  gt: '>',
  times: '×',
  cdot: '·',
  ldots: '…',
  dots: '…',
  cdots: '⋯',
  infty: '∞',
  in: '∈',
  notin: '∉',
  to: '→',
  rightarrow: '→',
  leftarrow: '←',
  pm: '±',
  mid: '|',
  oplus: '⊕',
  land: '∧',
  lor: '∨',
  neg: '¬',
  lfloor: '⌊',
  rfloor: '⌋',
  lceil: '⌈',
  rceil: '⌉',
  sum: 'Σ',
  prod: 'Π',
  sqrt: '√',
  alpha: 'α',
  beta: 'β',
  delta: 'δ',
  epsilon: 'ε',
  lambda: 'λ',
  sigma: 'σ',
  log: 'log',
  ln: 'ln',
  min: 'min',
  max: 'max',
  gcd: 'gcd',
  bmod: 'mod',
  mod: 'mod',
};

const SUPER: Record<string, string> = {
  '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
  '+': '⁺', '-': '⁻', n: 'ⁿ', i: 'ⁱ', k: 'ᵏ', m: 'ᵐ',
};

const SUB: Record<string, string> = {
  '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
  '+': '₊', '-': '₋', i: 'ᵢ', j: 'ⱼ', k: 'ₖ', n: 'ₙ', m: 'ₘ',
};

// every character mapped, or the script kept as source around its group
function script(body: string, map: Record<string, string>, mark: '^' | '_'): string {
  const chars = [...body];
  if (chars.every((one) => map[one] !== undefined)) return chars.map((one) => map[one]).join('');
  return chars.length === 1 ? `${mark}${body}` : `${mark}(${body})`;
}

/** One formula's TeX as Unicode text. */
export function texText(tex: string): string {
  return (
    tex
      .replace(/\\(?:text|mathrm|operatorname|mathit|mathbf)\{([^{}]*)\}/g, '$1')
      .replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, '$1/$2')
      .replace(/\\([%_#&$])/g, '$1')
      .replace(/\\[,;:! ]|\\q?quad/g, ' ')
      // a word such as `log` keeps a space from what follows it, as TeX spaces it
      .replace(/\\([a-zA-Z]+)(\s?)/g, (whole, name: string, space: string) => {
        const symbol = SYMBOLS[name];
        if (symbol === undefined) return whole;
        return /^[a-z]+$/.test(symbol) ? `${symbol} ` : `${symbol}${space}`;
      })
      .replace(/\^\{([^{}]*)\}|\^(\S)/g, (_, group: string | undefined, one: string | undefined) =>
        script(group ?? one ?? '', SUPER, '^'),
      )
      .replace(/_\{([^{}]*)\}|_(\S)/g, (_, group: string | undefined, one: string | undefined) =>
        script(group ?? one ?? '', SUB, '_'),
      )
      // grouping braces carry no text of their own
      .replace(/(?<!\\)[{}]/g, '')
      .replace(/\\([{}])/g, '$1')
      .replace(/ {2,}/g, ' ')
      .trim()
  );
}

// a markdown mark the converted text may carry, escaped so it reads as itself
const escaped = (text: string) => text.replace(/([*_`[\]\\])/g, '\\$1');

/**
 * Markdown with each `$…$` and `$$…$$` formula outside code read as Unicode
 * text. Code blocks and code spans are left as written.
 */
export function withMath(markdown: string): string {
  return markdown
    .split(/(```[\s\S]*?```|`[^`\n]*`)/g)
    .map((part, i) =>
      i % 2 === 1
        ? part
        : part
            .replace(/\$\$([\s\S]+?)\$\$/g, (_, tex: string) => escaped(texText(tex)))
            .replace(/\$(?=\S)([^$\n]*?\S)\$/g, (_, tex: string) => escaped(texText(tex))),
    )
    .join('');
}
