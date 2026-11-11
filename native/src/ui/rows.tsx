import { Fragment, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { Card, Divider, Text, TouchableRipple, useTheme } from 'react-native-paper';

import type { Stat } from '@algo-coach/core';
import { styles } from '@/ui/common';

/**
 * One pick on a list of picks. A phone is too narrow for the counts beside
 * the title, so they read on a line under it. Without `onPress` it opens nothing.
 */
export function PickRow(props: {
  title: string;
  badge?: string | null;
  stats: Stat[];
  // a line under the counts, such as the techniques a problem carries
  note?: string;
  // a note naming techniques reads in the code font
  mono?: boolean;
  // a row the user cannot act on yet, such as a locked lesson
  dim?: boolean;
  // a control at the row's right, such as a module's drag handle
  aside?: ReactNode;
  onPress?: () => void;
  onLongPress?: () => void;
}) {
  const theme = useTheme();
  const counts = props.stats.map((one) => (one.label ? `${one.value} ${one.label}` : String(one.value))).join(' · ');
  const text = (
    <View style={{ flex: 1, gap: 6 }}>
      <Text variant="titleMedium">{props.title}</Text>
      <View style={[styles.row, { flexWrap: 'wrap' }]}>
        {props.badge ? <Badge label={props.badge} /> : null}
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {counts}
        </Text>
      </View>
      {props.note ? (
        <Text
          variant="bodySmall"
          style={{ fontFamily: props.mono ? 'monospace' : undefined, color: theme.colors.onSurfaceVariant }}
        >
          {props.note}
        </Text>
      ) : null}
    </View>
  );
  const body = (
    <View
      style={[
        styles.row,
        { paddingLeft: 16, paddingRight: props.aside ? 4 : 16, paddingVertical: 12, opacity: props.dim ? 0.7 : 1 },
      ]}
    >
      {text}
      {props.aside}
    </View>
  );
  if (!props.onPress) return body;
  return (
    <TouchableRipple
      onPress={props.onPress}
      onLongPress={props.onLongPress}
      accessibilityRole="link"
      accessibilityLabel={props.title}
    >
      {body}
    </TouchableRipple>
  );
}

/** A small outlined label, sized to the meta line it sits in. */
export function Badge({ label }: { label: string }) {
  const theme = useTheme();
  return (
    <View
      style={{
        borderWidth: 1,
        borderColor: theme.colors.outline,
        borderRadius: 6,
        paddingHorizontal: 6,
        paddingVertical: 1,
      }}
    >
      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {label}
      </Text>
    </View>
  );
}

/** Rows in one bordered panel, divided by a hairline. */
export function PickPanel({ children }: { children: ReactNode[] }) {
  return (
    // one View: Card hands each direct child an `index`, which a Fragment refuses
    <Card mode="outlined">
      <View>
        {children.map((child, i) => (
          <Fragment key={i}>
            {i > 0 ? <Divider /> : null}
            {child}
          </Fragment>
        ))}
      </View>
    </Card>
  );
}

/**
 * One row of a panel a virtualised list draws item by item: the first item
 * carries the panel's top edge and the last its bottom, so the rows read as
 * one bordered panel, as `PickPanel` draws them.
 */
export function PanelItem({ first, last, children }: { first: boolean; last: boolean; children: ReactNode }) {
  const theme = useTheme();
  const radius = theme.roundness * 3;
  return (
    <View
      style={{
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.outlineVariant,
        borderLeftWidth: 1,
        borderRightWidth: 1,
        borderTopWidth: first ? 1 : StyleSheet.hairlineWidth,
        borderBottomWidth: last ? 1 : 0,
        borderTopLeftRadius: first ? radius : 0,
        borderTopRightRadius: first ? radius : 0,
        borderBottomLeftRadius: last ? radius : 0,
        borderBottomRightRadius: last ? radius : 0,
        overflow: 'hidden',
      }}
    >
      {children}
    </View>
  );
}
