import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useMemo } from 'react';
import { View } from 'react-native';
import { Button, IconButton, Text, useTheme } from 'react-native-paper';

import {
  type Board,
  type CertRecord,
  CLEAR_FOCUS,
  DUE_NOW,
  type Focus,
  FOCUS_CERT,
  FOCUS_NEXT,
  type FocusPart,
  focusView,
  LEARNING,
  NEW_LEFT,
  type Queue,
  RAISE_TODAY,
  focusTitle,
  STRICT,
  strictLabel,
} from '@algo-coach/core';

import { styles, tones } from './common';
import { Panel } from './rows';
import { Toggle } from './toggle';
import { useStore } from '@/lib/store';

// without the presses the card is a reading, as the Practice tab holds it:
// the focus's presses live on the knowledge home alone
interface Props {
  onMoreNew?: () => void; // raises today's new-question limit by NEW_STEP
  label: string;
  focus: Focus;
  b: Board; // built with the focus course included, as the focus queue uses
  queue: Queue;
  exams: CertRecord[];
  onClear?: () => void;
  onStrict?: () => void;
}

/** The focus as a card: what it covers, how far along it is, and what comes next. */
export function FocusCard(props: Props) {
  const { focus, b, queue } = props;
  const theme = useTheme();
  const tone = tones(theme.dark);
  const { now } = useStore();

  const info = useMemo(() => focusView(b, focus, queue, props.exams, now), [b, focus, queue, props.exams, now]);
  const color: Record<FocusPart, string> = {
    mastered: tone.done,
    learning: theme.colors.primary,
    // owed rather than held, so neutral, as the web's bar reads it
    review: theme.colors.outline,
    unseen: theme.colors.surfaceVariant,
  };
  const muted = { color: theme.colors.onSurfaceVariant };

  return (
    <Panel padded>
      <View style={{ gap: 8 }}>
        <View style={[styles.row, { gap: 4 }]}>
          <MaterialCommunityIcons
            name={focus.cert ? 'target' : 'crosshairs-gps'}
            size={20}
            color={theme.colors.primary}
          />
          <Text variant="titleSmall" numberOfLines={2} style={{ flex: 1 }}>
            {focusTitle(props.label)}
          </Text>
          {props.onStrict ? (
            <Toggle on={!!focus.strict} onPress={props.onStrict} accessibilityLabel={strictLabel(!!focus.strict)}>
              {STRICT}
            </Toggle>
          ) : null}
          {props.onClear ? (
            <IconButton
              icon="close"
              size={20}
              onPress={props.onClear}
              accessibilityLabel={CLEAR_FOCUS}
              style={{ margin: 0 }}
            />
          ) : null}
        </View>

        {info.total ? (
          <View
            style={{
              flexDirection: 'row',
              height: 8,
              borderRadius: 4,
              overflow: 'hidden',
              backgroundColor: theme.colors.surfaceVariant,
            }}
          >
            {info.parts.map((p) =>
              p.v ? <View key={p.k} style={{ flex: p.v, backgroundColor: color[p.k] }} /> : null,
            )}
          </View>
        ) : null}
        <Text variant="bodySmall" style={muted}>
          {info.summary}
        </Text>

        {/* wraps: the raise's label is longer than a phone's row holds beside the counts */}
        <View style={[styles.row, { gap: 16, flexWrap: 'wrap' }]}>
          <Stat icon="refresh" value={info.due} label={DUE_NOW} />
          {info.learning ? <Stat icon="timer-sand" value={info.learning} label={LEARNING} /> : null}
          <Stat icon="plus-circle-outline" value={info.newLeft} label={NEW_LEFT} />
          {props.onMoreNew ? (
            <Button compact mode="outlined" icon="plus" onPress={props.onMoreNew}>
              {RAISE_TODAY}
            </Button>
          ) : null}
        </View>

        {info.next ? (
          <Text variant="bodySmall">
            <Text style={muted}>{FOCUS_NEXT} </Text>
            {info.next}
          </Text>
        ) : null}
        {info.cert ? (
          <Text variant="bodySmall">
            <Text style={muted}>{FOCUS_CERT} </Text>
            {info.cert}
          </Text>
        ) : null}
      </View>
    </Panel>
  );
}

function Stat({ icon, value, label }: { icon: string; value: number; label: string }) {
  const theme = useTheme();
  return (
    <View style={[styles.row, { gap: 4 }]}>
      <MaterialCommunityIcons name={icon as 'refresh'} size={16} color={theme.colors.primary} />
      <Text variant="titleSmall">{value}</Text>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {label}
      </Text>
    </View>
  );
}
