import { Children, Fragment, type ReactNode } from 'react';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Pressable, type StyleProp, StyleSheet, View, type ViewStyle } from 'react-native';
import { Divider, ProgressBar, Text, TouchableRipple, useTheme } from 'react-native-paper';

import type { Stat } from '@climb/core';
import { styles } from '@/ui/common';
import { font, radius, space } from '@/ui/tokens';

/**
 * One pick on a list of picks. A phone is too narrow for the counts beside
 * the title, so they read on a line under it. Without `onPress` it opens nothing.
 */
export function PickRow(props: {
  title: string;
  // before the title: a rung's solved mark
  lead?: ReactNode;
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
  // how far a study has got, as one bar on every row that carries one: a
  // card's rungs solved, a module's questions passed
  progress?: { value: number; total: number; label: string } | null;
  // under the note and the bar: a card's trigger and its recall marks
  children?: ReactNode;
  onPress?: () => void;
  onLongPress?: () => void;
}) {
  const theme = useTheme();
  const counts = props.stats.map((one) => (one.label ? `${one.value} ${one.label}` : String(one.value))).join(' · ');
  const text = (
    <View style={{ flex: 1, gap: space[1.5] }}>
      {props.lead ? (
        <View style={styles.row}>
          {props.lead}
          <Text variant="titleMedium" style={{ flexShrink: 1 }}>
            {props.title}
          </Text>
        </View>
      ) : (
        <Text variant="titleMedium">{props.title}</Text>
      )}
      {props.badge || counts ? (
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          {props.badge ? <Badge label={props.badge} /> : null}
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {counts}
          </Text>
        </View>
      ) : null}
      {props.note ? (
        <Text
          variant="bodySmall"
          style={{ fontFamily: props.mono ? font.mono : undefined, color: theme.colors.onSurfaceVariant }}
        >
          {props.note}
        </Text>
      ) : null}
      {props.progress ? (
        <View style={{ maxWidth: ROW_BAR_WIDTH }}>
          <Progress {...props.progress} />
        </View>
      ) : null}
      {props.children}
    </View>
  );
  const body = (
    <View
      style={[
        styles.row,
        {
          paddingLeft: space[4],
          paddingRight: props.aside ? 4 : 16,
          paddingVertical: space[3],
          opacity: props.dim ? 0.7 : 1,
        },
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

// a row's bar stops short of the row's width, as the web's row bounds it
const ROW_BAR_WIDTH = 240;

/** How far a count has got, as one thin bar wherever a study's progress reads. */
export function Progress({ value, total, label }: { value: number; total: number; label: string }) {
  const theme = useTheme();
  return (
    <ProgressBar
      progress={total === 0 ? 0 : Math.min(1, value / total)}
      accessibilityLabel={`${label}: ${value} / ${total}`}
      style={{ borderRadius: radius(theme).full }}
    />
  );
}

/** One count and what it counts, read as a pair, as the web's `Stat`. */
export function Stat({ value, label }: { value: ReactNode; label: string }) {
  const theme = useTheme();
  return (
    <View>
      <Text variant="titleMedium">{value}</Text>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {label}
      </Text>
    </View>
  );
}

/** The counts of one panel, in a row that wraps. */
export function Stats({ children }: { children: ReactNode }) {
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', columnGap: space[6], rowGap: space[2] }}>{children}</View>
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
        borderRadius: radius(theme).md,
        paddingHorizontal: space[1.5],
        paddingVertical: space.px,
      }}
    >
      <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {label}
      </Text>
    </View>
  );
}

/**
 * A bordered block on the surface: every panel the phone draws, so a list,
 * a card's template and the focus read with one edge. `padded` holds prose
 * or controls; without it the rows inside run edge to edge.
 */
export function Panel({
  children,
  padded = false,
  style,
}: {
  children: ReactNode;
  padded?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const theme = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.outlineVariant,
          borderWidth: 1,
          borderRadius: radius(theme).xl,
          overflow: 'hidden',
          padding: padded ? 12 : 0,
          gap: padded ? 8 : 0,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

/** The strip heading a panel: it names what the panel holds, and where it names a record it opens it. */
export function PanelStrip({ children, onPress }: { children: ReactNode; onPress?: () => void }) {
  const theme = useTheme();
  const strip = (
    <View
      style={[
        styles.row,
        {
          paddingHorizontal: space[4],
          paddingVertical: space[3],
          borderBottomWidth: StyleSheet.hairlineWidth,
          borderColor: theme.colors.outlineVariant,
        },
      ]}
    >
      {children}
    </View>
  );
  return onPress ? (
    <TouchableRipple onPress={onPress} accessibilityRole="link">
      {strip}
    </TouchableRipple>
  ) : (
    strip
  );
}

/** Rows in one bordered panel, divided by a hairline. */
export function PickPanel({ children }: { children: ReactNode }) {
  return (
    <Panel>
      {Children.toArray(children).map((child, i) => (
        <Fragment key={i}>
          {i > 0 ? <Divider /> : null}
          {child}
        </Fragment>
      ))}
    </Panel>
  );
}

/**
 * One row of a panel a virtualised list draws item by item: the first item
 * carries the panel's top edge and the last its bottom, so the rows read as
 * one bordered panel, as `PickPanel` draws them.
 */
export function PanelItem({ first, last, children }: { first: boolean; last: boolean; children: ReactNode }) {
  const theme = useTheme();
  const edge = radius(theme).xl;
  return (
    <View
      style={{
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.outlineVariant,
        borderLeftWidth: 1,
        borderRightWidth: 1,
        borderTopWidth: first ? 1 : StyleSheet.hairlineWidth,
        borderBottomWidth: last ? 1 : 0,
        borderTopLeftRadius: first ? edge : 0,
        borderTopRightRadius: first ? edge : 0,
        borderBottomLeftRadius: last ? edge : 0,
        borderBottomRightRadius: last ? edge : 0,
        overflow: 'hidden',
      }}
    >
      {children}
    </View>
  );
}

/**
 * A section's heading and how many records it holds, the same on every
 * screen. `sub` heads a section inside another; `aside` sits at the right.
 * With `onToggle` the heading is the press that closes its own section.
 */
export function Heading(props: {
  title: string;
  count?: number;
  aside?: ReactNode;
  sub?: boolean;
  closed?: boolean;
  onToggle?: () => void;
}) {
  const theme = useTheme();
  const muted = theme.colors.onSurfaceVariant;
  const text = (
    <View style={[styles.row, { flex: 1, gap: space[1.5] }]}>
      {props.onToggle ? (
        <MaterialCommunityIcons name={props.closed ? 'chevron-right' : 'chevron-down'} size={20} color={muted} />
      ) : null}
      <Text variant={props.sub ? 'titleSmall' : 'titleMedium'} style={{ flexShrink: 1 }}>
        {props.title}
        {props.count !== undefined ? <Text style={{ color: muted }}>{`  ${props.count}`}</Text> : null}
      </Text>
    </View>
  );
  const aside =
    typeof props.aside === 'string' ? (
      <Text variant="bodySmall" style={{ color: muted, flexShrink: 1, textAlign: 'right' }}>
        {props.aside}
      </Text>
    ) : (
      props.aside
    );
  return (
    <View style={[styles.row, { marginTop: props.sub ? 0 : 8, minHeight: 32 }]}>
      {props.onToggle ? (
        <Pressable
          onPress={props.onToggle}
          accessibilityRole="button"
          accessibilityState={{ expanded: !props.closed }}
          style={{ flex: 1 }}
        >
          {text}
        </Pressable>
      ) : (
        text
      )}
      {aside}
    </View>
  );
}
