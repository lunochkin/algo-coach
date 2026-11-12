import { Children, isValidElement, useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

import { TABLE_GAP, tableShape } from '@algo-coach/core';

import { font, space } from '@/ui/tokens';

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

/**
 * How wide a rendered cell reads, in prose characters. Inline code is
 * monospace at its own size, so each of its characters counts `code` times
 * its size over the body's.
 */
export function nodeLength(node: ReactNode, code: number, body: number): number {
  if (typeof node === 'string' || typeof node === 'number') return String(node).length;
  if (Array.isArray(node)) return node.reduce((n: number, x: ReactNode) => n + nodeLength(x, code, body), 0);
  if (!isValidElement(node)) return 0;
  const props = node.props as { text?: unknown; size?: unknown; children?: ReactNode };
  if (typeof props.text === 'string') {
    const size = typeof props.size === 'number' ? props.size : body;
    return props.text.length * code * (size / body);
  }
  return Children.toArray(props.children).reduce((n: number, x) => n + nodeLength(x, code, body), 0);
}

/** A markdown table: a grid where its columns fit, a block per row otherwise (`pages.md`). */
export function ProseTable({ header, rows }: { header: ReactNode[][]; rows: ReactNode[][][] }) {
  const theme = useTheme();
  const [width, setWidth] = useState(0);
  const [char, setChar] = useState(0);
  const [mono, setMono] = useState(0);
  const heads = header.map(nodeText);
  const texts = rows.map((r) => r.map(nodeText));
  // rows until measured: a grid drawn first would flash, then reflow
  const cols = width && char && mono ? Math.floor(width / char) : 0;
  const grid = tableShape(heads, texts, cols) === 'grid';
  const body = theme.fonts.bodyLarge;
  // each column takes the share of the row its longest cell asks for, a code
  // character counted as wide as it draws
  const ratio = char && mono ? mono / char : 1;
  const len = (cell: ReactNode[] | undefined) => nodeLength(cell ?? [], ratio, body.fontSize);
  const want = header.map((h, i) => Math.max(len(h), ...rows.map((r) => len(r[i])), 1));
  // a column that fits a fair share takes the width its longest cell draws at,
  // the same in every row, so a short code cell never wraps; the longer
  // columns share what is left
  const fair = cols / Math.max(want.length, 1);
  const sized = want.map((w) =>
    w <= fair && want.some((o) => o > fair) ? { width: Math.ceil(w * char) + 2 } : { flex: w },
  );
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
      <Text
        style={[body, { position: 'absolute', opacity: 0, fontFamily: font.mono }]}
        onTextLayout={(e) => {
          const first = e.nativeEvent.lines[0];
          if (first?.text.length) setMono(first.width / first.text.length);
        }}
      >
        {PROBE}
      </Text>
      {grid ? (
        <View>
          <View style={[styles.gridRow, { gap: TABLE_GAP * char }]}>
            {heads.map((h, j) => (
              <Text key={j} style={[body, sized[j], { fontWeight: '600' }]}>
                {h}
              </Text>
            ))}
          </View>
          {rows.map((row, i) => (
            <View key={i} style={[styles.gridRow, { gap: TABLE_GAP * char, borderTopWidth: 1 }, rule]}>
              {row.map((c, j) => (
                <View key={j} style={sized[j]}>
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
