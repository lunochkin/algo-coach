import { python } from '@codemirror/lang-python';
import type { SyntaxNode, Tree } from '@lezer/common';

// the names a file declares, which the phone's keyboard offers back:
// `flows.md`, Drill loop. A name the file only reads, such as `len`, is the
// library's, and is never offered

const PARSER = python().language.parser;

// a name binds where it stands between the opening keyword and the one that
// ends the target: `for x in`, `with f as fh`, `except E as err`
function between(node: SyntaxNode, opens: string[], closes: string | null): boolean {
  let before = node.prevSibling;
  while (before && !opens.includes(before.name) && before.name !== closes) before = before.prevSibling;
  if (!before || before.name === closes) return false;
  if (closes === null) return true;
  for (let after = node.nextSibling; after; after = after.nextSibling) if (after.name === closes) return true;
  return false;
}

// before the statement's last assignment operator, so `x = y` binds `x` alone
function assigned(node: SyntaxNode, operator: string): boolean {
  for (let after = node.nextSibling; after; after = after.nextSibling) if (after.name === operator) return true;
  return false;
}

function binds(node: SyntaxNode): boolean {
  const parent = node.parent;
  if (!parent) return false;
  switch (parent.name) {
    case 'ImportStatement':
    case 'FunctionDefinition':
    case 'ClassDefinition':
    case 'ParamList':
      return true;
    case 'AssignStatement':
      return assigned(node, 'AssignOp');
    case 'UpdateStatement':
      return assigned(node, 'UpdateOp');
    case 'NamedExpression':
      return node.prevSibling === null;
    case 'ForStatement':
    case 'ArrayComprehensionExpression':
    case 'SetComprehensionExpression':
    case 'DictionaryComprehensionExpression':
    case 'ComprehensionExpression':
      return between(node, ['for'], 'in');
    case 'WithStatement':
    case 'TryStatement':
      return between(node, ['as'], null);
    default:
      return false;
  }
}

/** Every name the code declares, once each, in the order they first appear. */
export function declaredNames(code: string, tree: Tree = PARSER.parse(code)): string[] {
  const seen = new Set<string>();
  tree.iterate({
    enter: (ref) => {
      if (ref.name !== 'VariableName') return;
      if (binds(ref.node)) seen.add(code.slice(ref.from, ref.to));
    },
  });
  return [...seen];
}

/** The part of a name typed just before the caret, which a name pressed replaces. */
export const wordBefore = (line: string) => /[A-Za-z_][A-Za-z0-9_]*$/.exec(line)?.[0] ?? '';

/**
 * The names the row offers: those starting with the word being typed, the
 * word itself left out, or every declared name where nothing is being typed.
 */
export function offered(names: string[], typing: string): string[] {
  if (typing === '') return names;
  return names.filter((one) => one !== typing && one.startsWith(typing));
}
