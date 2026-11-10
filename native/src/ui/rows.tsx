import { Fragment, type ReactNode } from 'react';
import { View } from 'react-native';
import { Card, Divider, Text, TouchableRipple, useTheme } from 'react-native-paper';

import type { Stat } from '@algo-coach/core';
import { styles } from '@/ui/common';

/**
 * One pick on a list of picks. A phone is too narrow for the counts beside
 * the title, so they read on a line under it. Without `onPress` it opens nothing.
 */
export function PickRow(props: { title: string; badge?: string | null; stats: Stat[]; onPress?: () => void }) {
  const theme = useTheme();
  const counts = props.stats.map((one) => (one.label ? `${one.value} ${one.label}` : String(one.value))).join(' · ');
  const body = (
    <View style={{ paddingHorizontal: 16, paddingVertical: 12, gap: 6 }}>
      <Text variant="titleMedium">{props.title}</Text>
      <View style={[styles.row, { flexWrap: 'wrap' }]}>
        {props.badge ? <Badge label={props.badge} /> : null}
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {counts}
        </Text>
      </View>
    </View>
  );
  if (!props.onPress) return body;
  return (
    <TouchableRipple onPress={props.onPress} accessibilityRole="link" accessibilityLabel={props.title}>
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
