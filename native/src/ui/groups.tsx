import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Pressable, View } from 'react-native';
import { Button, IconButton, Text, useTheme } from 'react-native-paper';

import {
  aimedAt,
  aimFocus,
  type Board,
  type CellState,
  type Course,
  MODULE_FOCUS,
  MODULE_FOCUSED,
  moduleGrid,
  MODULE_START,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { styles, tones } from '@/ui/common';
import { PageSection, type Sections } from '@/ui/sections';
import type { Scope } from '@/ui/start';
import { space } from '@/ui/tokens';

/**
 * A module's groups, a table of subtopics by level per topic. Each scope
 * starts a filtered queue, and each subtopic carries its own focus press:
 * `pages.md`, The knowledge pages.
 */
export function ModuleGroups({
  c,
  b,
  of,
  onStart,
}: {
  c: Course;
  b: Board;
  of: Sections;
  onStart: (s: Scope) => void;
}) {
  const st = useStore();
  const theme = useTheme();
  const { done, open } = tones(theme.dark);
  const tone: Record<CellState, string> = {
    covered: done,
    open,
    locked: theme.colors.onSurfaceDisabled,
    empty: theme.colors.onSurfaceDisabled,
  };
  const grid = moduleGrid(b, c);
  const aimed = (topic: string | null, sub: string | null) => aimedAt(st.focus, c.slug, topic, sub);
  const aim = (topic: string | null, sub: string | null) =>
    void st.setFocus(aimFocus(st.focus, { course: c.slug, topic, sub }));

  return (
    <View style={{ gap: space[4] }}>
      {grid.topics.map((t) => (
        <PageSection
          key={t.slug}
          of={of}
          id={t.slug}
          title={t.title}
          count={t.count}
          body="bare"
          aside={
            <>
              <Button
                compact
                icon="play"
                onPress={() => onStart({ course: c.slug, topic: t.slug, sub: null, level: null })}
              >
                {MODULE_START}
              </Button>
              <Button compact icon="crosshairs-gps" disabled={aimed(t.slug, null)} onPress={() => aim(t.slug, null)}>
                {aimed(t.slug, null) ? MODULE_FOCUSED : MODULE_FOCUS}
              </Button>
            </>
          }
        >
          <View style={[styles.row, { paddingLeft: space[1] }]}>
            <View style={{ flex: 1 }} />
            {grid.levels.map((l) => (
              <Text key={l.level} variant="labelSmall" style={cellStyle}>
                {l.name}
              </Text>
            ))}
          </View>
          {t.rows.map((row) => (
            <View key={row.sub} style={styles.row}>
              {/* the name starts the subtopic at every level; the press beside it aims the focus */}
              <Pressable
                style={{ flex: 1, minHeight: 40, justifyContent: 'center' }}
                accessibilityRole="button"
                accessibilityLabel={row.start}
                onPress={() => onStart({ course: c.slug, topic: t.slug, sub: row.sub, level: null })}
              >
                <Text
                  variant="bodyMedium"
                  numberOfLines={1}
                  style={aimed(t.slug, row.sub) ? { color: theme.colors.primary } : null}
                >
                  {row.title}
                </Text>
              </Pressable>
              <IconButton
                icon="crosshairs-gps"
                size={18}
                selected={aimed(t.slug, row.sub)}
                iconColor={aimed(t.slug, row.sub) ? theme.colors.primary : theme.colors.onSurfaceVariant}
                accessibilityLabel={row.focus}
                onPress={() => aim(t.slug, row.sub)}
                style={{ margin: space[0] }}
              />
              {row.cells.map(({ level, cell, label }) => {
                return (
                  // a locked cell starts too: locks do not apply to the filtered queue
                  <Pressable
                    key={level}
                    disabled={cell.state === 'empty'}
                    accessibilityLabel={label}
                    onPress={() => onStart({ course: c.slug, topic: t.slug, sub: row.sub, level })}
                    style={{
                      width: 48,
                      minHeight: 40,
                      flexDirection: 'row',
                      justifyContent: 'flex-end',
                      alignItems: 'center',
                      gap: space[0.5],
                    }}
                  >
                    {cell.state === 'locked' ? (
                      <MaterialCommunityIcons name="lock-outline" size={12} color={theme.colors.onSurfaceDisabled} />
                    ) : null}
                    <Text variant="bodySmall" style={{ fontVariant: ['tabular-nums'], color: tone[cell.state] }}>
                      {cell.count}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          ))}
        </PageSection>
      ))}
    </View>
  );
}

const cellStyle = { width: 48, textAlign: 'right' as const };
