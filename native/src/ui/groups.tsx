import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Pressable, View } from 'react-native';
import { Button, IconButton, Text, useTheme } from 'react-native-paper';

import {
  type Board,
  type CellState,
  type Course,
  focusOn,
  groupCell,
  levelName,
  levels,
  MODULE_FOCUS,
  MODULE_FOCUSED,
  MODULE_START,
  startGroup,
  subsByDepth,
  subTitle,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { styles, tones } from '@/ui/common';
import type { Scope } from '@/ui/start';

/**
 * A module's groups, a table of subtopics by level per topic. Each scope
 * starts a filtered queue, and each subtopic carries its own focus press:
 * `pages.md`, The knowledge pages.
 */
export function ModuleGroups({ c, b, onStart }: { c: Course; b: Board; onStart: (s: Scope) => void }) {
  const st = useStore();
  const theme = useTheme();
  const { done, open } = tones(theme.dark);
  const tone: Record<CellState, string> = {
    covered: done,
    open,
    locked: theme.colors.onSurfaceDisabled,
    empty: theme.colors.onSurfaceDisabled,
  };
  const lv = levels(b.rules);
  const aimed = (topic: string | null, sub: string | null) =>
    st.focus?.course === c.slug && !st.focus.cert && st.focus.topic === topic && st.focus.sub === sub;
  const aim = (topic: string | null, sub: string | null) =>
    void st.setFocus({ course: c.slug, topic, sub, strict: !!st.focus?.strict });

  return (
    <View style={{ gap: 16 }}>
      {c.topics.map((t) => (
        <View key={t.slug} style={{ gap: 4 }}>
          <View style={styles.row}>
            <Text variant="titleSmall" style={{ flex: 1 }}>
              {t.title}
            </Text>
            <Button
              compact
              icon="play"
              onPress={() => onStart({ course: c.slug, topic: t.slug, sub: null, level: null })}
            >
              {MODULE_START}
            </Button>
            <Button compact disabled={aimed(t.slug, null)} onPress={() => aim(t.slug, null)}>
              {aimed(t.slug, null) ? MODULE_FOCUSED : MODULE_FOCUS}
            </Button>
          </View>
          <View style={[styles.row, { paddingLeft: 4 }]}>
            <View style={{ flex: 1 }} />
            {lv.map((l) => (
              <Text key={l} variant="labelSmall" style={cellStyle}>
                {levelName(b.rules, l, true)}
              </Text>
            ))}
          </View>
          {subsByDepth(c, t).map((sub) => (
            <View key={sub} style={styles.row}>
              {/* the name starts the subtopic at every level; the press beside it aims the focus */}
              <Pressable
                style={{ flex: 1, minHeight: 40, justifyContent: 'center' }}
                accessibilityRole="button"
                accessibilityLabel={`Start ${subTitle(c, sub)}`}
                onPress={() => onStart({ course: c.slug, topic: t.slug, sub, level: null })}
              >
                <Text
                  variant="bodyMedium"
                  numberOfLines={1}
                  style={aimed(t.slug, sub) ? { color: theme.colors.primary } : null}
                >
                  {subTitle(c, sub)}
                </Text>
              </Pressable>
              <IconButton
                icon="crosshairs-gps"
                size={18}
                selected={aimed(t.slug, sub)}
                iconColor={aimed(t.slug, sub) ? theme.colors.primary : theme.colors.onSurfaceVariant}
                accessibilityLabel={focusOn(subTitle(c, sub))}
                onPress={() => aim(t.slug, sub)}
                style={{ margin: 0 }}
              />
              {lv.map((level) => {
                const cell = groupCell(b, { course: c.slug, topic: t.slug, sub, level });
                return (
                  // a locked cell starts too: locks do not apply to the filtered queue
                  <Pressable
                    key={level}
                    disabled={cell.state === 'empty'}
                    accessibilityLabel={startGroup(subTitle(c, sub), levelName(b.rules, level), cell.line)}
                    onPress={() => onStart({ course: c.slug, topic: t.slug, sub, level })}
                    style={{
                      width: 48,
                      minHeight: 40,
                      flexDirection: 'row',
                      justifyContent: 'flex-end',
                      alignItems: 'center',
                      gap: 2,
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
        </View>
      ))}
    </View>
  );
}

const cellStyle = { width: 48, textAlign: 'right' as const };
