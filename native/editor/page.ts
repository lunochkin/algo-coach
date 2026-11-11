// the page the phone's editor WebView loads: the shared Python setup, typed
// through the app's keyboard. `just editor-page` bundles it into
// `src/editor/page.ts`, which the app ships
import { type EditorKey, keyed, pythonEditing } from '@algo-coach/editor';
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
      '.cm-activeLine, .cm-activeLineGutter': { backgroundColor: colors.active },
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
        // the app's keyboard types, and the system's never opens
        EditorView.contentAttributes.of({
          inputmode: 'none',
          autocapitalize: 'off',
          autocorrect: 'off',
          spellcheck: 'false',
        }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) post({ kind: 'change', doc: update.state.doc.toString() });
        }),
        look(colors),
      ],
    }),
  });
  view.focus();
}

function press(key: EditorKey) {
  if (!view) return;
  const made = keyed(view.state, key);
  if (made) view.dispatch(made);
}

function receive(event: MessageEvent) {
  const message = JSON.parse(String(event.data)) as FromApp;
  if (message.kind === 'open') open(message.doc, message.colors);
  else if (message.kind === 'key') press(message.key);
}

// Android delivers the app's messages on the document, iOS on the window
window.addEventListener('message', receive);
document.addEventListener('message', receive as unknown as EventListener);
post({ kind: 'ready' });
