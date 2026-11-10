import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useMemo } from 'react';
import { View } from 'react-native';
import { Chip, IconButton, Text, TouchableRipple, useTheme } from 'react-native-paper';

import { type Board, type CertRecord, counted, type Focus, type FocusPart, focusView, NEW_STEP, type Queue } from '@algo-coach/core';

import { styles, tones } from './common';

interface Props {
  onMoreNew: () => void; // raises today's new-question limit by NEW_STEP
  label: string;
  focus: Focus;
  b: Board; // built with the focus course included, as the focus queue uses
  queue: Queue;
  exams: CertRecord[];
  onOpen: () => void;
  onClear: () => void;
  onStrict: () => void;
}

/** The focus as a card: what it covers, how far along it is, and what comes next. */
export function FocusCard(props: Props) {
  const { focus, b, queue } = props;
  const theme = useTheme();
  const tone = tones(theme.dark);

  const info = useMemo(() => focusView(b, focus, queue, props.exams, Date.now()), [b, focus, queue, props.exams]);
  const color: Record<FocusPart, string> = {
    mastered: tone.done,
    learning: theme.colors.primary,
    review: tone.open,
    unseen: theme.colors.surfaceVariant,
  };
  const mastered = info.parts.find((p) => p.k === 'mastered')?.v ?? 0;
  const muted = { color: theme.colors.onSurfaceVariant };

  return (
    <TouchableRipple
      onPress={props.onOpen}
      borderless
      accessibilityRole="button"
      accessibilityLabel={`Focus: ${props.label}. ${counted(info.total, 'question')}, ${mastered} mastered, ${info.due} to review now, ${info.newLeft} new left today`}
      accessibilityHint="Opens the map on the focus"
      style={{ borderRadius: 16, backgroundColor: theme.colors.elevation.level2, padding: 12 }}>
      <View style={{ gap: 8 }}>
        <View style={[styles.row, { gap: 4 }]}>
          <MaterialCommunityIcons name={focus.cert ? 'target' : 'crosshairs-gps'} size={20} color={theme.colors.primary} />
          <Text variant="titleSmall" numberOfLines={2} style={{ flex: 1 }}>
            {props.label}
          </Text>
          <Chip
            compact
            selected={!!focus.strict}
            showSelectedCheck
            onPress={props.onStrict}
            accessibilityLabel={focus.strict ? 'Strict focus on: reviews from the focus only' : 'Strict focus off: reviews from everywhere'}>
            Strict
          </Chip>
          <IconButton icon="close" size={20} onPress={props.onClear} accessibilityLabel="Clear focus" style={{ margin: 0 }} />
        </View>

        {info.total ? (
          <View style={{ flexDirection: 'row', height: 8, borderRadius: 4, overflow: 'hidden', backgroundColor: theme.colors.surfaceVariant }}>
            {info.parts.map((p) => (p.v ? <View key={p.k} style={{ flex: p.v, backgroundColor: color[p.k] }} /> : null))}
          </View>
        ) : null}
        <Text variant="bodySmall" style={muted}>
          {info.summary}
        </Text>

        <View style={[styles.row, { gap: 16 }]}>
          <Stat icon="refresh" value={info.due} label="to review now" />
          {info.learning ? <Stat icon="timer-sand" value={info.learning} label="learning" /> : null}
          <Stat icon="plus-circle-outline" value={info.newLeft} label="new left today" />
          <Chip
            compact
            icon="plus"
            onPress={props.onMoreNew}
            accessibilityLabel={`Allow ${NEW_STEP} more new questions today`}>
            {`${NEW_STEP}`}
          </Chip>
        </View>

        {info.next ? (
          <Text variant="bodySmall">
            <Text style={muted}>Next: </Text>
            {info.next}
          </Text>
        ) : null}
        {info.cert ? (
          <Text variant="bodySmall">
            <Text style={muted}>Certificate: </Text>
            {info.cert}
          </Text>
        ) : null}
      </View>
    </TouchableRipple>
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
