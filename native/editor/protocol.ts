import type { EditorKey } from '@algo-coach/editor';

// what the app and the editor page say to each other, one JSON message each

export interface Colors {
  dark: boolean;
  background: string;
  foreground: string;
  muted: string;
  gutter: string;
  active: string;
  selection: string;
  keyword: string;
  name: string;
  string: string;
  number: string;
  comment: string;
}

export type FromApp =
  | { kind: 'open'; doc: string; colors: Colors }
  | { kind: 'key'; key: EditorKey }
  // the WebView changed size: the page lays itself out again only on its next input
  | { kind: 'measure' };

export type FromPage =
  | { kind: 'ready' }
  | { kind: 'change'; doc: string }
  // the declared names the row offers, narrowed to the word before the caret
  | { kind: 'names'; names: string[] };
