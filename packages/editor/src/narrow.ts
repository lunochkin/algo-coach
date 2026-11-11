import { RangeSetBuilder, type Extension } from '@codemirror/state';
import { Decoration, type DecorationSet, EditorView, ViewPlugin, type ViewUpdate } from '@codemirror/view';

// a phone fits some forty characters, and a median canonical's widest line is
// fifty-five: each leading space is drawn half wide, so a level of four
// spaces reads as two, and the file keeps its four
export const SPACE_SCALE = 0.5;
// a wrapped line's continuation sits this much deeper than the line itself,
// so it does not read as the next statement
export const HANG_CH = 2;

export const leadingSpaces = (text: string) => /^ */.exec(text)![0].length;

/** The style hanging a wrapped line under its own indent, drawn narrow. */
export function hangStyle(spaces: number): string {
  const hang = spaces * SPACE_SCALE + HANG_CH;
  return `padding-left: calc(${hang}ch + 6px); text-indent: -${hang}ch`;
}

const narrowSpace = Decoration.mark({ class: 'cm-narrow-indent' });

function decorate(view: EditorView): DecorationSet {
  const built = new RangeSetBuilder<Decoration>();
  for (const { from, to } of view.visibleRanges) {
    for (let pos = from; pos <= to;) {
      const line = view.state.doc.lineAt(pos);
      const spaces = leadingSpaces(line.text);
      built.add(line.from, line.from, Decoration.line({ attributes: { style: hangStyle(spaces) } }));
      if (spaces > 0) built.add(line.from, line.from + spaces, narrowSpace);
      pos = line.to + 1;
    }
  }
  return built.finish();
}

/** Narrow indentation and hanging wraps, for an editor a phone's width holds. */
export function narrowIndent(): Extension {
  return [
    EditorView.lineWrapping,
    ViewPlugin.fromClass(
      class {
        decorations: DecorationSet;
        constructor(view: EditorView) {
          this.decorations = decorate(view);
        }
        update(update: ViewUpdate) {
          if (update.docChanged || update.viewportChanged) this.decorations = decorate(update.view);
        }
      },
      { decorations: (plugin) => plugin.decorations },
    ),
    EditorView.theme({ '.cm-narrow-indent': { letterSpacing: `-${1 - SPACE_SCALE}ch` } }),
  ];
}
