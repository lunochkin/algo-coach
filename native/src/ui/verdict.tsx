import { useEffect, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

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
} from '@algo-coach/core';
import { tones } from '@/ui/common';

type Submitted = components['schemas']['Submitted'];
type Outcome = components['schemas']['CaseOutcome'];

// a colour per outcome: a wrong answer and a timeout are different remedies,
// so they never share one
function outcomeColor(outcome: Outcome, dark: boolean, error: string): string {
  if (outcome === 'passed') return tones(dark).done;
  if (outcome === 'wrong') return error;
  if (outcome === 'timeout') return dark ? '#ffb74d' : '#a15c00';
  return dark ? '#ce93d8' : '#7b1fa2';
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
    <Text variant="titleMedium" style={{ fontFamily: 'monospace' }} accessibilityLabel={ELAPSED_TIME}>
      {duration(shownSeconds(elapsedSec, receivedAt, now, running && elapsedSec !== null))}
    </Text>
  );
}

// a value cut on screen past this many characters: a separating case weighs
// up to a mebibyte, and drawing it whole stalls the screen
const SHOWN = 2_000;

/** A submission read back: the verdict, a mark per case, and the first failing case whole. */
export function SubmissionVerdict({ submitted }: { submitted: Submitted }) {
  const theme = useTheme();
  const view = submissionView(submitted);
  const results = submitted.verification.results ?? [];
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <View style={{ gap: 6 }}>
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
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 4 }} accessibilityLabel={CASES_IN_ORDER}>
        {results.map((one, index) => (
          <View
            key={one.case_id}
            accessibilityLabel={`case ${index + 1}: ${OUTCOME_LABELS[one.outcome]}`}
            style={{
              width: 12,
              height: 12,
              borderRadius: 3,
              backgroundColor: outcomeColor(one.outcome, theme.dark, theme.colors.error),
            }}
          />
        ))}
      </View>
      {view.failure ? (
        <View style={{ gap: 4 }}>
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

function Value({ label, text }: { label: string; text: string }) {
  const theme = useTheme();
  return (
    <View style={{ gap: 2 }}>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {label}
      </Text>
      <ScrollView
        horizontal
        style={{ backgroundColor: theme.colors.surfaceVariant, borderRadius: 6 }}
        contentContainerStyle={{ padding: 6 }}
      >
        <Text selectable style={{ fontFamily: 'monospace', fontSize: 13, color: theme.colors.onSurfaceVariant }}>
          {text.length > SHOWN ? `${text.slice(0, SHOWN)}…` : text}
        </Text>
      </ScrollView>
    </View>
  );
}
