import { useEffect, useState } from 'react';
import * as Clipboard from 'expo-clipboard';
import { ScrollView, View } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';

import {
  duration,
  FAILURE_ARGS,
  FAILURE_ERROR,
  FAILURE_EXPECTED,
  FAILURE_RETURNED,
  OUTCOME_LABELS,
  shownSeconds,
  submissionView,
  type components,
  ELAPSED_TIME,
  CASES_IN_ORDER,
  caseLabel,
  cutValue,
  CUT_VALUE,
  showAllKb,
  COPY,
} from '@algo-coach/core';
import { font, palette, radius, space, textSize } from '@/ui/tokens';

type Submitted = components['schemas']['Submitted'];
type Outcome = components['schemas']['CaseOutcome'];

// a colour per outcome: a wrong answer and a timeout are different remedies,
// so they never share one
function outcomeColor(outcome: Outcome, dark: boolean, error: string): string {
  if (outcome === 'wrong') return error;
  return palette(dark)[outcome];
}

/**
 * The elapsed time, ticking while the clock runs. Its own component: it
 * renders every second, and the editor beside it must not.
 */
export function ElapsedClock({
  elapsedSec,
  receivedAt,
  running,
}: {
  elapsedSec: number | null;
  receivedAt: number;
  running: boolean;
}) {
  const [now, setNow] = useState(() => performance.now());
  useEffect(() => {
    if (!running) return;
    const tick = setInterval(() => setNow(performance.now()), 1000);
    return () => clearInterval(tick);
  }, [running]);
  return (
    <Text variant="titleMedium" style={{ fontFamily: font.mono }} accessibilityLabel={ELAPSED_TIME}>
      {duration(shownSeconds(elapsedSec, receivedAt, now, running && elapsedSec !== null))}
    </Text>
  );
}

/** A submission read back: the verdict, a mark per case, and the first failing case whole. */
export function SubmissionVerdict({ submitted }: { submitted: Submitted }) {
  const theme = useTheme();
  const view = submissionView(submitted);
  const results = submitted.verification.results ?? [];
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <View style={{ gap: space[1.5] }}>
      <Text
        variant="titleSmall"
        style={{ color: view.overall ? outcomeColor(view.overall, theme.dark, theme.colors.error) : undefined }}
      >
        {view.verdict}
      </Text>
      {view.failures ? (
        <Text variant="bodySmall" style={muted}>
          {view.failures}
        </Text>
      ) : null}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space[1] }} accessibilityLabel={CASES_IN_ORDER}>
        {results.map((one, index) => (
          <View
            key={one.case_id}
            accessibilityLabel={caseLabel(index, OUTCOME_LABELS[one.outcome], one.elapsed_ms)}
            style={{
              width: 12,
              height: 12,
              borderRadius: radius(theme).sm,
              backgroundColor: outcomeColor(one.outcome, theme.dark, theme.colors.error),
            }}
          />
        ))}
      </View>
      {view.failure ? (
        <View style={{ gap: space[1] }}>
          <Text
            variant="labelLarge"
            style={{ color: outcomeColor(view.failure.outcome, theme.dark, theme.colors.error) }}
          >
            {view.failure.title}
          </Text>
          <Value label={FAILURE_ARGS} text={JSON.stringify(view.failure.args)} />
          <Value label={FAILURE_EXPECTED} text={JSON.stringify(view.failure.expected)} />
          {view.failure.outcome === 'wrong' ? (
            <Value label={FAILURE_RETURNED} text={JSON.stringify(view.failure.returned)} />
          ) : null}
          {view.failure.error ? <Value label={FAILURE_ERROR} text={view.failure.error} /> : null}
        </View>
      ) : null}
    </View>
  );
}

// a long value reads cut until the reader asks for it whole, and copies whole
// either way, as on the web
function Value({ label, text }: { label: string; text: string }) {
  const theme = useTheme();
  const [whole, setWhole] = useState(false);
  const shown = cutValue(text, whole);
  return (
    <View style={{ gap: space[0.5] }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: space[1] }}>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {label}
        </Text>
        {shown.long ? (
          <>
            <Button compact onPress={() => setWhole(!whole)}>
              {whole ? CUT_VALUE : showAllKb(text.length)}
            </Button>
            <Button compact onPress={() => void Clipboard.setStringAsync(text)}>
              {COPY}
            </Button>
          </>
        ) : null}
      </View>
      <ScrollView
        horizontal
        style={{ backgroundColor: theme.colors.surfaceVariant, borderRadius: radius(theme).md }}
        contentContainerStyle={{ padding: space[1.5] }}
      >
        <Text
          selectable
          style={{ fontFamily: font.mono, fontSize: textSize.codeInline, color: theme.colors.onSurfaceVariant }}
        >
          {shown.text}
        </Text>
      </ScrollView>
    </View>
  );
}
