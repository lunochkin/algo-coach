import type { ReactNode } from 'react';
import { View } from 'react-native';
import { Chip } from 'react-native-paper';

import { styles } from '@/ui/common';

/**
 * Every selectable chip the phone draws: a filter, a choice in a sheet, the
 * focus's Strict. On reads filled and off reads outlined, with no check, as
 * the web's toggle groups read. A chip that opens a page is a link instead.
 */
export function Toggle(props: {
  on: boolean;
  onPress: () => void;
  icon?: string;
  accessibilityLabel?: string;
  children: ReactNode;
}) {
  return (
    <Chip
      compact
      mode={props.on ? 'flat' : 'outlined'}
      selected={props.on}
      showSelectedCheck={false}
      icon={props.icon}
      onPress={props.onPress}
      accessibilityLabel={props.accessibilityLabel}
    >
      {props.children}
    </Chip>
  );
}

/** Toggles in a row that wraps, as one group of choices reads. */
export function Toggles({ children }: { children: ReactNode }) {
  return <View style={[styles.row, { flexWrap: 'wrap' }]}>{children}</View>;
}
