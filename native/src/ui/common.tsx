import { useState, type ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';

import { router } from 'expo-router';

import { block, type ExamPlan, type Queue, syncErrorSummary, syncLine, RETRY } from '@algo-coach/core';
import type { ExamSession, QueueSession, Session, SyncState } from '@/lib/store';

/** Monospace, horizontally scrollable, never wrapped. `verbatim` keeps leading spaces (diagrams). */
export function CodeBlock({ code, verbatim = false }: { code: string; verbatim?: boolean }) {
  const theme = useTheme();
  return (
    <ScrollView
      horizontal
      persistentScrollbar
      style={[styles.code, { backgroundColor: theme.colors.surfaceVariant }]}
      contentContainerStyle={styles.codeInner}
    >
      <Text selectable style={[styles.mono, { color: theme.colors.onSurfaceVariant }]}>
        {verbatim ? code.replace(/\s+$/, '') : block(code)}
      </Text>
    </ScrollView>
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
      accessibilityLabel={`Sync error: ${syncErrorSummary(sync.error)}. Tap for details.`}
      style={{
        minHeight: 48,
        justifyContent: 'center',
        padding: 12,
        borderRadius: 12,
        backgroundColor: theme.colors.errorContainer,
      }}
    >
      <Text variant="bodyMedium" style={{ color: theme.colors.onErrorContainer }}>
        {syncErrorSummary(sync.error)}
      </Text>
      {open ? (
        <Text variant="bodySmall" selectable style={{ marginTop: 4, color: theme.colors.onErrorContainer }}>
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
  code: { borderRadius: 8, marginVertical: 8 },
  codeInner: { padding: 12 },
  mono: { fontFamily: 'monospace', fontSize: 14 },
  page: { padding: 16, gap: 12 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
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
        paddingHorizontal: 16,
        paddingTop: 12,
        paddingBottom: bottom + 16,
        gap: 8,
        backgroundColor: theme.colors.background,
      }}
    >
      {above}
      <View style={{ gap: 8, flexDirection: row ? 'row' : 'column' }}>{children}</View>
    </View>
  );
}

/** Progress colours readable in light and dark mode: covered (done) and open (unlocked). */
export const tones = (dark: boolean) =>
  dark ? { done: '#81c784', open: '#ffb74d' } : { done: '#2e7d32', open: '#a15c00' };

/** A read from the engine that failed, with the press that asks again. */
export function Failed({ message, onRetry }: { message: string; onRetry: () => void }) {
  const theme = useTheme();
  return (
    <View style={{ gap: 8, alignItems: 'flex-start' }}>
      <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
        {message}
      </Text>
      <Button mode="outlined" onPress={onRetry}>
        {RETRY}
      </Button>
    </View>
  );
}
