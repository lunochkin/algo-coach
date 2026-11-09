import { python } from '@codemirror/lang-python'
import { highlightTree, tagHighlighter, tags } from '@lezer/highlight'

// one mapping of Python's tags to the theme's five code tokens, read by both
// the editor a sitting is typed into and a template's form on a card. The
// classes are styled once in `index.css`
export const HIGHLIGHTER = tagHighlighter([
  { tag: [tags.keyword, tags.operatorKeyword], class: 'tok-keyword' },
  {
    tag: [tags.function(tags.variableName), tags.definition(tags.variableName)],
    class: 'tok-name',
  },
  { tag: [tags.string, tags.special(tags.string)], class: 'tok-string' },
  { tag: [tags.number, tags.bool, tags.null], class: 'tok-number' },
  { tag: tags.comment, class: 'tok-comment' },
])

const PARSER = python().language.parser

export type Piece = { text: string; token?: string }

// a form parsed into spans, so a card renders it without mounting an editor:
// the editor is a few hundred kilobytes to show ten lines that take no input
export function pieces(code: string): Piece[] {
  const tree = PARSER.parse(code)
  const out: Piece[] = []
  let at = 0
  highlightTree(tree, HIGHLIGHTER, (from, to, token) => {
    if (from > at) out.push({ text: code.slice(at, from) })
    out.push({ text: code.slice(from, to), token })
    at = to
  })
  if (at < code.length) out.push({ text: code.slice(at) })
  return out
}
