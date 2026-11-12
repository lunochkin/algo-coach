import { Children, isValidElement, useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

import { TABLE_GAP, tableShape } from '@algo-coach/core';

import { space } from '@/ui/tokens';

// a character of prose, averaged over ordinary words
const PROBE = 'the quick brown fox jumps over the lazy dog';

/** The text a rendered cell reads as; inline code carries it as `text`. */
export function nodeText(node: ReactNode): string {
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(nodeText).join('');
  if (!isValidElement(node)) return '';
  const props = node.props as { text?: unknown; children?: ReactNode };
  if (typeof props.text === 'string') return props.text;
  return Children.toArray(props.children).map(nodeText).join('');
}

/** A markdown table: a grid where its columns fit, a block per row otherwise (`pages.md`). */
export function ProseTable({ header, rows }: { header: ReactNode[][]; rows: ReactNode[][][] }) {
  const theme = useTheme();
  const [width, setWidth] = useState(0);
  const [char, setChar] = useState(0);
  const heads = header.map(nodeText);
  const texts = rows.map((r) => r.map(nodeText));
  const cols = width && char ? Math.floor(width / char) : Infinity;
  const grid = tableShape(heads, texts, cols) === 'grid';
  // each column takes the share of the row its longest cell asks for
  const flex = heads.map((h, i) => Math.max(h.length, ...texts.map((r) => r[i]?.length ?? 0), 1));
  const body = theme.fonts.bodyLarge;
  const muted = { color: theme.colors.onSurfaceVariant };
  const rule = { borderColor: theme.colors.outlineVariant };
  const cell = (nodes: ReactNode[]) => <Text style={[body, { color: theme.colors.onSurface }]}>{nodes}</Text>;

  return (
    <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
      <Text
        style={[body, { position: 'absolute', opacity: 0 }]}
        onTextLayout={(e) => {
          const first = e.nativeEvent.lines[0];
          if (first?.text.length) setChar(first.width / first.text.length);
        }}
      >
        {PROBE}
      </Text>
      {grid ? (
        <View>
          <View style={[styles.gridRow, { gap: TABLE_GAP * char }]}>
            {heads.map((h, j) => (
              <Text key={j} style={[body, { flex: flex[j], fontWeight: '600' }]}>
                {h}
              </Text>
            ))}
          </View>
          {rows.map((row, i) => (
            <View key={i} style={[styles.gridRow, { gap: TABLE_GAP * char, borderTopWidth: 1 }, rule]}>
              {row.map((c, j) => (
                <View key={j} style={{ flex: flex[j] }}>
                  {cell(c)}
                </View>
              ))}
            </View>
          ))}
        </View>
      ) : (
        <View style={{ gap: space[3] }}>
          {rows.map((row, i) => (
            <View key={i} style={[{ borderLeftWidth: 2, paddingLeft: space[3] }, rule]}>
              {cell(row[0] ?? [])}
              {row.slice(1).map((c, j) => (
                <Text key={j} style={[body, { color: theme.colors.onSurface }]}>
                  {heads[j + 1]?.trim() ? <Text style={muted}>{heads[j + 1]}: </Text> : null}
                  {c}
                </Text>
              ))}
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  gridRow: { flexDirection: 'row', paddingVertical: space[1] },
});
