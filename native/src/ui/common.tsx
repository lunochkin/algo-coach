import { useMemo, useState, type ReactNode } from 'react';
import { Pressable, ScrollView, type StyleProp, StyleSheet, type TextStyle, View, type ViewStyle } from 'react-native';
import { Appbar, Button, type ButtonProps, Text, useTheme } from 'react-native-paper';

import { router } from 'expo-router';

import {
  block,
  codeRows,
  WRAP_MARK,
  type ExamPlan,
  type Queue,
  RETRY,
  syncErrorSummary,
  syncLine,
  syncErrorLabel,
  pageReading,
  copyReading,
} from '@climb/core';
import type { QueueSession, Session, SyncState } from '@/lib/store';
import { font, palette, radius, space, textSize } from '@/ui/tokens';

/**
 * Monospace. `wrap` breaks a long line into rows that continue under its own
 * indent behind a mark, and otherwise the block scrolls sideways (diagrams).
 * `verbatim` keeps the common indent.
 */
export function CodeBlock({
  code,
  verbatim = false,
  wrap = false,
  flush = false,
}: {
  code: string;
  verbatim?: boolean;
  wrap?: boolean;
  // inside prose, where the gap between blocks spaces it
  flush?: boolean;
}) {
  const theme = useTheme();
  const text = verbatim ? code.replace(/\s+$/, '') : block(code);
  const mono = [styles.mono, { color: theme.colors.onSurfaceVariant }];
  const shape = [
    flush ? null : styles.code,
    { borderRadius: radius(theme).lg, backgroundColor: theme.colors.surfaceVariant },
  ];
  if (wrap) return <WrappedCode text={text} mono={mono} shape={shape} />;
  return (
    <ScrollView horizontal persistentScrollbar style={shape} contentContainerStyle={styles.codeInner}>
      <Text selectable style={mono}>
        {text}
      </Text>
    </ScrollView>
  );
}

const PROBE = 'M'.repeat(40);

function WrappedCode(props: { text: string; mono: StyleProp<TextStyle>; shape: StyleProp<ViewStyle> }) {
  const theme = useTheme();
  const [width, setWidth] = useState(0);
  const [char, setChar] = useState(0);
  // the rows are cut in core, so the phone and the web break a line alike
  const cols = width && char ? Math.floor(width / char) : Infinity;
  const rows = useMemo(() => codeRows(props.text, cols), [props.text, cols]);
  return (
    <View style={[props.shape, styles.codeInner]}>
      <Text
        style={[props.mono, { position: 'absolute', opacity: 0 }]}
        onTextLayout={(e) => {
          // the probe wraps in a narrow block, so its first line holds fewer
          const first = e.nativeEvent.lines[0];
          if (first?.text.length) setChar(first.width / first.text.length);
        }}
      >
        {PROBE}
      </Text>
      <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
        {rows.map((row, i) => (
          <View key={i} style={{ flexDirection: 'row' }}>
            {row.indent ? <Text style={props.mono}>{row.indent}</Text> : null}
            {row.cont ? <Text style={[props.mono, { color: theme.colors.outline }]}>{WRAP_MARK}</Text> : null}
            <Text selectable style={[props.mono, { flex: 1 }]}>
              {row.text || ' '}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

/** Sync error shown where it can be read: top of the screen, tap for the full message. */
export function SyncBanner({ sync }: { sync: SyncState }) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  if (!sync.error || sync.running) return null;
  return (
    <Pressable
      onPress={() => setOpen(!open)}
      accessibilityRole="button"
      accessibilityLabel={syncErrorLabel(syncErrorSummary(sync.error))}
      style={{
        minHeight: 48,
        justifyContent: 'center',
        padding: space[3],
        borderRadius: radius(theme).xl,
        backgroundColor: theme.colors.errorContainer,
      }}
    >
      <Text variant="bodyMedium" style={{ color: theme.colors.onErrorContainer }}>
        {syncErrorSummary(sync.error)}
      </Text>
      {open ? (
        <Text variant="bodySmall" selectable style={{ marginTop: space[1], color: theme.colors.onErrorContainer }}>
          {sync.error}
        </Text>
      ) : null}
    </Pressable>
  );
}

export function SyncLine({ sync, showError = true }: { sync: SyncState; showError?: boolean }) {
  const theme = useTheme();
  const text = syncLine(sync, Date.now());
  return (
    <View>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {text}
      </Text>
      {showError && sync.error && !sync.running ? (
        <Text variant="bodySmall" style={{ color: theme.colors.error }} numberOfLines={3}>
          {syncErrorSummary(sync.error)}
        </Text>
      ) : null}
    </View>
  );
}

export const styles = StyleSheet.create({
  code: { marginVertical: space[2] },
  codeInner: { padding: space[3] },
  mono: { fontFamily: font.mono, fontSize: textSize.code },
  page: { padding: space.gutter, gap: space.stack },
  row: { flexDirection: 'row', alignItems: 'center', gap: space[2] },
});

type Starter = { setSession: (s: Session) => void };

/** Opens the quiz on a continuous queue; `course` is the board selection its picks use. */
export function startQueue(
  st: Starter,
  mode: QueueSession['mode'],
  queue: Queue,
  course: string | null,
  include: string | null = null,
) {
  st.setSession({ mode, queue, course, include });
  router.push('/quiz');
}

export function startExam(st: Starter, plan: ExamPlan) {
  st.setSession(plan);
  router.push('/quiz');
}

/** Bottom action bar with an opaque background, so scrolled content never shows behind the buttons. */
export function BottomBar({
  bottom,
  row = false,
  above,
  children,
}: {
  bottom: number;
  row?: boolean;
  // drawn over the presses, as the app's keyboard is
  above?: ReactNode;
  children: ReactNode;
}) {
  const theme = useTheme();
  return (
    <View
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        paddingHorizontal: space[4],
        paddingTop: space[3],
        paddingBottom: bottom + 16,
        gap: space[2],
        backgroundColor: theme.colors.background,
      }}
    >
      {above}
      <View style={{ gap: space[2], flexDirection: row ? 'row' : 'column' }}>{children}</View>
    </View>
  );
}

/**
 * A press in a screen's bottom bar, as the web's `Button`: the act in the
 * primary fill, and a press beside it at a lower weight through `mode`.
 */
export function Press({ mode = 'contained', ...props }: Omit<ButtonProps, 'contentStyle'>) {
  return <Button mode={mode} contentStyle={{ paddingVertical: space[2] }} {...props} />;
}

/** Progress colours in either scheme: covered (done) and open (unlocked), from the phone's tokens. */
export const tones = (dark: boolean) => ({ done: palette(dark).passed, open: palette(dark).timeout });

/**
 * A screen's header, as the web's `PageHeader`: the way back, the title, what
 * sits beside it, and the note under it. A tab's root carries no way back;
 * a running queue's way back is its Stop.
 */
export function ScreenHeader({
  title,
  back = { onPress: () => router.back() },
  aside,
  note = [],
}: {
  title: string;
  back?: { onPress: () => void; close?: string } | null;
  aside?: ReactNode;
  note?: (string | null | undefined)[];
}) {
  return (
    <>
      <Appbar.Header>
        {back?.close ? (
          <Appbar.Action icon="close" onPress={back.onPress} accessibilityLabel={back.close} />
        ) : back ? (
          <Appbar.BackAction onPress={back.onPress} />
        ) : null}
        <Appbar.Content title={title} />
        {aside}
      </Appbar.Header>
      <HeaderNote lines={note} />
    </>
  );
}

/**
 * The lines identifying what a screen's title names, under the header bar,
 * as the web's PageHeader carries its note: a card's technique, a lesson's
 * module and minutes, a module's counts.
 */
export function HeaderNote({ lines }: { lines: (string | null | undefined)[] }) {
  const theme = useTheme();
  const shown = lines.filter((line): line is string => !!line);
  if (!shown.length) return null;
  return (
    <View style={{ paddingHorizontal: space[4], paddingBottom: space[2], gap: space[0.5] }}>
      {shown.map((line) => (
        <Text key={line} variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {line}
        </Text>
      ))}
    </View>
  );
}

/** A refusal or a failure, the same wherever it shows, as the web's ErrorLine. */
export function ErrorLine({ children }: { children: ReactNode }) {
  const theme = useTheme();
  return (
    <Text variant="bodySmall" style={{ color: theme.colors.error }}>
      {children}
    </Text>
  );
}

/** The empty reading, as `Loaded` draws it: a list or a record holding nothing. */
export function Blank({ children }: { children: ReactNode }) {
  const theme = useTheme();
  return (
    <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
      {children}
    </Text>
  );
}

/** What a screen loads, from the engine or the device's copy: the data, or why it is missing. */
export interface Reading<T> {
  data: T | null | undefined;
  error: string | null | undefined;
  reload: () => void;
}

/**
 * The three readings a screen gives before its content, rendered once, as
 * the web's `Loaded` renders them: a screen loading, failed or empty then
 * reads the same whichever screen it is. `of` names what is loaded.
 */
export function Loaded<T>(props: {
  of: string;
  state: Reading<T>;
  blank?: string;
  blankWhen?: (data: T) => boolean;
  children: (data: T) => ReactNode;
}) {
  const theme = useTheme();
  const shown = pageReading(props.of, props.state, props.blank, props.blankWhen);
  if (shown.kind === 'failed') return <Failed message={shown.line} onRetry={props.state.reload} />;
  if (shown.kind === 'blank') return <Blank>{shown.line}</Blank>;
  if (shown.kind === 'loading')
    return (
      <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
        {shown.line}
      </Text>
    );
  return <>{props.children(shown.data)}</>;
}

/** The device's copy as a reading: held once ready, failed with the sync while it holds nothing. */
export function fromCopy<T>(
  st: { ready: boolean; sync: SyncState; requestSync: (ms: number) => void },
  data: T | null | undefined,
): Reading<T> {
  return { ...copyReading(st.ready, st.sync.error, data), reload: () => st.requestSync(0) };
}

export function Failed({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={{ gap: space[2], alignItems: 'flex-start' }}>
      <ErrorLine>{message}</ErrorLine>
      <Button mode="outlined" onPress={onRetry}>
        {RETRY}
      </Button>
    </View>
  );
}
