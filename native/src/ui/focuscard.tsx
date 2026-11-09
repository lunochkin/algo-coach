import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useMemo } from 'react';
import { View } from 'react-native';
import { Chip, IconButton, Text, TouchableRipple, useTheme } from 'react-native-paper';

import {
  certStates,
  focusScope,
  levelName,
  type Board,
  type CertRecord,
  type Focus,
  type Queue,
} from '@/core';

import { STATE_LABEL } from './certs';
import { styles, tones } from './common';

interface Props {
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

  const info = useMemo(() => {
    const now = Date.now();
    const qs = focusScope(b, focus);
    const inScope = new Set(qs);
    const n = { mastered: 0, learning: 0, review: 0, unseen: 0, locked: 0 };
    for (const q of qs) {
      const s = b.status(q, now);
      if (s === 'mastered') n.mastered++;
      else if (s === 'learning') n.learning++;
      else if (s === 'unseen') {
        n.unseen++;
        if (!b.unlocked(q)) n.locked++;
      } else n.review++;
    }
    const c = b.course(focus.course);
    // The first open level with new work inside the focus: what Continue is working through.
    const next = c
      ? b.frontier(c).find((g) => b.groupQuestions(g).some((q) => inScope.has(q)))
      : undefined;
    const cert = focus.cert && c ? certStates(b, c, props.exams).get(focus.cert) : undefined;
    return {
      total: qs.length,
      n,
      due: queue.reviews(b, now).length,
      newLeft: queue.newLeft(b, now),
      next: next && { label: `${next.sub} · ${levelName(b.rules, next.level)}`, passed: b.nPassed(next), of: b.groupQuestions(next).length },
      cert,
    };
  }, [b, focus, queue, props.exams]);

  const { n, total } = info;
  const parts = [
    { k: 'mastered', v: n.mastered, color: tone.done, label: 'mastered' },
    { k: 'learning', v: n.learning, color: theme.colors.primary, label: 'learning' },
    { k: 'review', v: n.review, color: tone.open, label: 'to review' },
    { k: 'unseen', v: n.unseen, color: theme.colors.surfaceVariant, label: 'unseen' },
  ];
  const muted = { color: theme.colors.onSurfaceVariant };

  return (
    <TouchableRipple
      onPress={props.onOpen}
      borderless
      accessibilityRole="button"
      accessibilityLabel={`Focus: ${props.label}. ${total} questions, ${n.mastered} mastered, ${info.due} to review now, ${info.newLeft} new left today`}
      accessibilityHint="Opens Practice on the focus"
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

        {total ? (
          <View style={{ flexDirection: 'row', height: 8, borderRadius: 4, overflow: 'hidden', backgroundColor: theme.colors.surfaceVariant }}>
            {parts.map((p) => (p.v ? <View key={p.k} style={{ flex: p.v, backgroundColor: p.color }} /> : null))}
          </View>
        ) : null}
        <Text variant="bodySmall" style={muted}>
          {`${total} questions · ${parts
            .filter((p) => p.v)
            .map((p) => `${p.v} ${p.label}`)
            .join(' · ')}${n.locked ? ` (${n.locked} locked)` : ''}`}
        </Text>

        <View style={[styles.row, { gap: 16 }]}>
          <Stat icon="refresh" value={info.due} label="to review now" />
          <Stat icon="plus-circle-outline" value={info.newLeft} label="new left today" />
        </View>

        {info.next ? (
          <Text variant="bodySmall">
            <Text style={muted}>Next: </Text>
            {`${info.next.label} · ${info.next.passed}/${info.next.of}`}
          </Text>
        ) : null}
        {info.cert ? (
          <Text variant="bodySmall">
            <Text style={muted}>Certificate: </Text>
            {`${STATE_LABEL[info.cert.state]} · coverage ${Math.round(info.cert.coverage * 100)}% · retention ${Math.round(info.cert.retention * 100)}%`}
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
