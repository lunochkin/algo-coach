// the page the phone's editor WebView loads: the shared Python setup, typed
// through the app's keyboard. `just editor-page` bundles it into
// `src/editor/page.ts`, which the app ships
import {
  declaredNames,
  type EditorKey,
  keyed,
  narrowIndent,
  offered,
  pythonEditing,
  wordBefore,
} from '@climb/editor';
import { syntaxTree } from '@codemirror/language';
import { EditorState } from '@codemirror/state';
import { drawSelection, EditorView } from '@codemirror/view';

import type { Colors, FromApp } from './protocol';

declare global {
  interface Window {
    ReactNativeWebView: { postMessage: (data: string) => void };
  }
}

const post = (message: object) => window.ReactNativeWebView.postMessage(JSON.stringify(message));

let view: EditorView | null = null;

function look(colors: Colors) {
  const css = `
    html, body, #editor { margin: 0; height: 100%; background: ${colors.background}; }
    .tok-keyword { color: ${colors.keyword}; }
    .tok-name { color: ${colors.name}; }
    .tok-string { color: ${colors.string}; }
    .tok-number { color: ${colors.number}; }
    .tok-comment { color: ${colors.comment}; font-style: italic; }`;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);
  return EditorView.theme(
    {
      '&': { height: '100%', fontSize: '15px', backgroundColor: colors.background, color: colors.foreground },
      '.cm-scroller': { fontFamily: 'monospace' },
      '.cm-content': { padding: '8px 0' },
      '.cm-gutters': { backgroundColor: colors.gutter, color: colors.muted, border: 'none' },
      // translucent, so a selection drawn beneath the caret's line still shows
      '.cm-activeLine': { backgroundColor: `color-mix(in srgb, ${colors.active} 55%, transparent)` },
      '.cm-activeLineGutter': { backgroundColor: colors.active },
      // drawn whether or not the page has focus: the keys are the app's, so
      // the WebView is never tapped and the browser's own caret never shows
      '.cm-cursorLayer .cm-cursor': {
        display: 'block',
        borderLeftColor: colors.foreground,
        borderLeftWidth: '2px',
      },
      '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
        backgroundColor: colors.selection,
      },
    },
    { dark: colors.dark },
  );
}

function open(doc: string, colors: Colors) {
  view?.destroy();
  view = new EditorView({
    parent: document.getElementById('editor')!,
    state: EditorState.create({
      doc,
      selection: { anchor: doc.length },
      extensions: [
        ...pythonEditing(),
        drawSelection(),
        narrowIndent(),
        // the app's keyboard types, and the system's never opens
        EditorView.contentAttributes.of({
          inputmode: 'none',
          autocapitalize: 'off',
          autocorrect: 'off',
          spellcheck: 'false',
        }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) post({ kind: 'change', doc: update.state.doc.toString() });
          if (update.docChanged || update.selectionSet) names(update.state);
        }),
        look(colors),
      ],
    }),
  });
  view.focus();
  lastNames = '';
  names(view.state);
}

// sent only where the row would change, so a caret moving inside one word
// costs no message
let lastNames = '';
function names(state: EditorState) {
  const doc = state.doc.toString();
  const head = state.selection.main.head;
  const line = state.doc.lineAt(head);
  const row = offered(declaredNames(doc, syntaxTree(state)), wordBefore(line.text.slice(0, head - line.from)));
  const key = row.join(' ');
  if (key === lastNames) return;
  lastNames = key;
  post({ kind: 'names', names: row });
}

function press(key: EditorKey) {
  if (!view) return;
  const made = keyed(view.state, key);
  if (made) view.dispatch(made);
}

// the editor grew or shrank. Shrunk, the caret's line may sit under the new
// edge. Grown, a scroll offset past the new end stays until the next touch,
// which leaves the top of a file that now fits out of view
function fit() {
  if (!view) return;
  view.dispatch({ effects: EditorView.scrollIntoView(view.state.selection.main.head, { y: 'nearest' }) });
  view.requestMeasure({
    read: (v) => v.scrollDOM.scrollHeight - v.scrollDOM.clientHeight,
    write: (most, v) => {
      if (v.scrollDOM.scrollTop > most) v.scrollDOM.scrollTop = Math.max(0, most);
    },
  });
}

function receive(event: MessageEvent) {
  const message = JSON.parse(String(event.data)) as FromApp;
  if (message.kind === 'open') open(message.doc, message.colors);
  else if (message.kind === 'key') press(message.key);
  else if (message.kind === 'measure') fit();
  else if (message.kind === 'replace' && view)
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: message.doc },
      selection: { anchor: message.doc.length },
      scrollIntoView: true,
    });
}

// Android delivers the app's messages on the document, iOS on the window
window.addEventListener('message', receive);
document.addEventListener('message', receive as unknown as EventListener);
post({ kind: 'ready' });
