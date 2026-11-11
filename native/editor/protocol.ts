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

export type FromApp = { kind: 'open'; doc: string; colors: Colors } | { kind: 'key'; key: EditorKey };

export type FromPage = { kind: 'ready' } | { kind: 'change'; doc: string };
