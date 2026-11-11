import { type ComponentType, type Ref, useImperativeHandle, useRef } from 'react';
import { useTheme } from 'react-native-paper';
import { WebView, type WebViewMessageEvent, type WebViewProps } from 'react-native-webview';

import type { Colors, FromApp, FromPage } from '../../editor/protocol';
import { PAGE } from '@/editor/page';
import type { Key } from '@/lib/keys';

// the WebView's own types resolve its props to `never` under this React, so
// the component is read through the props it is given here
type PageHandle = { postMessage: (data: string) => void };
const Page = WebView as unknown as ComponentType<WebViewProps & { ref?: Ref<PageHandle> }>;

// the web's five code tokens, so a form reads in one palette on both clients
const TOKENS = {
  light: {
    keyword: 'oklch(0.48 0.16 290)',
    name: 'oklch(0.48 0.13 250)',
    string: 'oklch(0.5 0.12 150)',
    number: 'oklch(0.52 0.12 60)',
    comment: 'oklch(0.53 0.02 260)',
    selection: 'oklch(0.86 0.06 250)',
  },
  dark: {
    keyword: 'oklch(0.78 0.13 290)',
    name: 'oklch(0.8 0.1 250)',
    string: 'oklch(0.8 0.12 150)',
    number: 'oklch(0.82 0.11 70)',
    comment: 'oklch(0.65 0.02 260)',
    selection: 'oklch(0.45 0.08 250)',
  },
};

export interface EditorHandle {
  press: (key: Key) => void;
  // after the editor's height changed, so the page lays itself out again
  measure: () => void;
}

/**
 * The phone's Python editor: CodeMirror in a WebView, set up as the web's is,
 * typed through the app's keyboard. `README.md` gives why the editor alone is
 * a WebView.
 */
export function CodeEditor({
  initial,
  onChange,
  ref,
}: {
  initial: string;
  onChange: (code: string) => void;
  ref?: Ref<EditorHandle>;
}) {
  const theme = useTheme();
  const page = useRef<PageHandle>(null);
  const send = (message: FromApp) => page.current?.postMessage(JSON.stringify(message));
  useImperativeHandle(ref, () => ({
    press: (key) => send({ kind: 'key', key }),
    measure: () => send({ kind: 'measure' }),
  }));

  const colors: Colors = {
    dark: theme.dark,
    background: theme.colors.surface,
    foreground: theme.colors.onSurface,
    muted: theme.colors.onSurfaceVariant,
    gutter: theme.colors.surfaceVariant,
    active: theme.colors.elevation.level2,
    ...TOKENS[theme.dark ? 'dark' : 'light'],
  };

  const receive = (event: WebViewMessageEvent) => {
    const message = JSON.parse(event.nativeEvent.data) as FromPage;
    // the document is sent once the page can take it, and never again: a
    // second send would move the caret under the user's typing
    if (message.kind === 'ready') send({ kind: 'open', doc: initial, colors });
    else onChange(message.doc);
  };

  return (
    <Page
      ref={page}
      originWhitelist={['*']}
      source={{ html: PAGE }}
      onMessage={receive}
      textZoom={100}
      overScrollMode="never"
      setBuiltInZoomControls={false}
      style={{ flex: 1, backgroundColor: theme.colors.surface }}
    />
  );
}
