import { Fragment, type ReactNode } from 'react';
import { View } from 'react-native';
import { Card, Chip, Divider, Text, TouchableRipple, useTheme } from 'react-native-paper';

import type { Stat } from '@algo-coach/core';
import { styles } from '@/ui/common';

/** One pick on a list of picks, the counts at its right. Without `onPress` it reads and opens nothing. */
export function PickRow(props: { title: string; badge?: string | null; stats: Stat[]; onPress?: () => void }) {
  const theme = useTheme();
  const counts = props.stats.map((one) => (one.label ? `${one.value} ${one.label}` : String(one.value))).join(' · ');
  const body = (
    <View style={[styles.row, { paddingHorizontal: 16, paddingVertical: 12 }]}>
      <Text variant="titleMedium" style={{ flexShrink: 1 }}>
        {props.title}
      </Text>
      {props.badge ? (
        <Chip compact mode="outlined">
          {props.badge}
        </Chip>
      ) : null}
      <Text variant="bodySmall" style={{ marginLeft: 'auto', color: theme.colors.onSurfaceVariant }}>
        {counts}
      </Text>
    </View>
  );
  if (!props.onPress) return body;
  return (
    <TouchableRipple onPress={props.onPress} accessibilityRole="link" accessibilityLabel={props.title}>
      {body}
    </TouchableRipple>
  );
}

/** Rows in one bordered panel, divided by a hairline. */
export function PickPanel({ children }: { children: ReactNode[] }) {
  return (
    <Card mode="outlined">
      {children.map((child, i) => (
        <Fragment key={i}>
          {i > 0 ? <Divider /> : null}
          {child}
        </Fragment>
      ))}
    </Card>
  );
}
