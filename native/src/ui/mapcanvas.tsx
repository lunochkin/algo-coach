// The map drawn with Skia: GPU drawing each frame, no view-sized bitmap. react-native-svg
// rasterised the whole graph into one huge bitmap and re-uploaded it on every selection (~2 s).
// Canvas children run in Skia's own reconciler, where React context (useTheme) does not reach:
// the theme is passed in as a prop.
import {
  Canvas,
  Circle,
  DashPathEffect,
  Group,
  matchFont,
  Path,
  RoundedRect,
  Skia,
  Text as SkText,
  type SkFont,
} from '@shopify/react-native-skia';
import { memo, useMemo } from 'react';
import { Platform, StyleSheet } from 'react-native';
import { useTheme, type MD3Theme } from 'react-native-paper';
import { useDerivedValue, type SharedValue } from 'react-native-reanimated';

import {
  cut,
  entryMark,
  lessonNode,
  lessonSlug,
  MAP_DIMS,
  subTitle,
  type Board,
  type ClusterBox,
  type Course,
  type EdgePath,
} from '@algo-coach/core';

import { tones } from './common';

// the sizes the core lays the map out at
export const NODE_W = MAP_DIMS.nodeW;
export const NODE_H = MAP_DIMS.nodeH;

export interface Placed {
  sub: string; // subtopic slug, "lesson:<slug>" or a certificate id
  kind: 'quiz' | 'lesson' | 'cert';
  topic: string;
  x: number;
  y: number;
}

const family = Platform.select({ android: 'sans-serif', default: 'System' });
const fonts: Record<number, SkFont> = {};
function font(size: number): SkFont {
  return (fonts[size] ??= matchFont({ fontFamily: family, fontSize: size }));
}

/** A certificate node's level pips: one per certified level, coloured by its state. */
export interface CertPip {
  letter: string; // F, A, P, E
  color: string;
  filled: boolean; // earned
}

interface Props {
  nodes: Placed[];
  edges: EdgePath[];
  clusters: ClusterBox[];
  titles: Map<string, string>; // topic slug (or "all") -> title
  outside: Map<string, string[]>; // subtopics with prerequisites in other topics
  picked: string | null;
  lit: Set<string> | null;
  dots: Map<string, (string | null)[]>;
  c: Course;
  b: Board;
  pips: Map<string, CertPip[]>; // "cert:<scope>" -> its levels
  tx: SharedValue<number>;
  ty: SharedValue<number>;
  scale: SharedValue<number>;
}

export function MapCanvas(props: Props) {
  const { nodes, edges, picked, lit, tx, ty, scale, clusters } = props;
  const theme = useTheme();
  const transform = useDerivedValue(() => [{ translateX: tx.value }, { translateY: ty.value }, { scale: scale.value }]);
  const paths = useMemo(
    () =>
      edges.flatMap(({ edge: e, d, dash }) => {
        const p = Skia.Path.MakeFromSVGString(d);
        return p ? [{ e, p, dash }] : [];
      }),
    [edges],
  );
  return (
    <Canvas style={StyleSheet.absoluteFill}>
      <Group transform={transform}>
        {clusters.map((k) => {
          const on = !lit || lit.has(`cluster:${k.topic}`);
          return (
            <Group key={k.topic} opacity={on ? 1 : 0.35}>
              <RoundedRect x={k.x} y={k.y} width={k.w} height={k.h} r={18} color={theme.colors.surface} />
              <RoundedRect
                x={k.x}
                y={k.y}
                width={k.w}
                height={k.h}
                r={18}
                style="stroke"
                strokeWidth={1}
                color={theme.colors.outlineVariant}
              />
              <SkText
                x={k.x + 16}
                y={k.y + 22}
                text={props.titles.get(k.topic) ?? k.topic}
                font={font(14)}
                color={theme.colors.primary}
              />
            </Group>
          );
        })}
        {paths.map(({ e, p, dash }) => {
          const on = !lit || (lit.has(e.from) && lit.has(e.to));
          const hi = on && !!lit;
          return (
            <Path
              key={`${e.from}>${e.to}`}
              path={p}
              style="stroke"
              strokeWidth={hi ? 2 : 1.2}
              color={
                hi
                  ? theme.colors.primary
                  : e.kind === 'teaches'
                    ? theme.colors.tertiary
                    : e.from.startsWith('cert:')
                      ? theme.colors.secondary
                      : theme.colors.outline
              }
              opacity={on ? 0.9 : 0.12}
            >
              {dash ? <DashPathEffect intervals={dash} /> : null}
            </Path>
          );
        })}
        {nodes.map((n) => {
          const opacity = lit && !lit.has(n.sub) ? 0.2 : 1;
          const sel = n.sub === picked;
          return n.kind === 'cert' ? (
            <CertNode
              key={n.sub}
              theme={theme}
              n={n}
              title={props.titles.get(n.topic) ?? n.topic}
              pips={props.pips.get(n.sub) ?? []}
              picked={sel}
              opacity={opacity}
            />
          ) : n.kind === 'lesson' ? (
            <LessonNode key={n.sub} theme={theme} n={n} c={props.c} b={props.b} picked={sel} opacity={opacity} />
          ) : (
            <QuizNode
              key={n.sub}
              theme={theme}
              n={n}
              title={subTitle(props.c, n.sub)}
              picked={sel}
              opacity={opacity}
              dots={props.dots.get(n.sub) ?? []}
              entry={props.outside.has(n.sub)}
            />
          );
        })}
      </Group>
    </Canvas>
  );
}

const QuizNode = memo(function QuizNode(props: {
  theme: MD3Theme;
  n: Placed;
  title: string;
  picked: boolean;
  opacity: number;
  dots: (string | null)[];
  entry: boolean; // has prerequisites in other topics
}) {
  const { n, picked, theme } = props;
  return (
    <Group opacity={props.opacity}>
      <RoundedRect
        x={n.x}
        y={n.y}
        width={NODE_W}
        height={NODE_H}
        r={12}
        color={picked ? theme.colors.secondaryContainer : theme.colors.surfaceVariant}
      />
      <RoundedRect
        x={n.x}
        y={n.y}
        width={NODE_W}
        height={NODE_H}
        r={12}
        style="stroke"
        strokeWidth={picked ? 2 : 1}
        color={picked ? theme.colors.primary : theme.colors.outlineVariant}
      />
      <SkText x={n.x + 12} y={n.y + 22} text={cut(props.title, 21)} font={font(13)} color={theme.colors.onSurface} />
      {props.entry ? (
        // Entry mark: this subtopic also needs subtopics of other topics (through the certificate edge).
        <Path path={entryMark(n)} style="stroke" strokeWidth={2} color={theme.colors.secondary} />
      ) : null}
      {props.dots.map((fill, i) => (
        <Group key={i}>
          {fill ? <Circle cx={n.x + 18 + i * 16} cy={n.y + NODE_H - 14} r={5} color={fill} /> : null}
          <Circle
            cx={n.x + 18 + i * 16}
            cy={n.y + NODE_H - 14}
            r={5}
            style="stroke"
            strokeWidth={1.2}
            color={fill ?? theme.colors.outline}
          />
        </Group>
      ))}
    </Group>
  );
});

const LessonNode = memo(function LessonNode(props: {
  theme: MD3Theme;
  n: Placed;
  c: Course;
  b: Board;
  picked: boolean;
  opacity: number;
}) {
  const { n, c, b, picked, theme } = props;
  const tone = tones(theme.dark);
  const x = c.graph?.lesson(lessonSlug(n.sub)!);
  if (!x) return null;
  const state = b.lessonState(c, x);
  const color = state === 'done' ? tone.done : state === 'available' ? tone.open : theme.colors.onSurfaceDisabled;
  const line = Skia.Path.MakeFromSVGString(`M${n.x + 12},${n.y + 3} L${n.x + 12},${n.y + NODE_H - 3}`);
  return (
    <Group opacity={props.opacity}>
      <RoundedRect
        x={n.x}
        y={n.y}
        width={NODE_W}
        height={NODE_H}
        r={4}
        color={picked ? theme.colors.secondaryContainer : theme.colors.tertiaryContainer}
        opacity={picked ? 1 : 0.55}
      />
      <RoundedRect
        x={n.x}
        y={n.y}
        width={NODE_W}
        height={NODE_H}
        r={4}
        style="stroke"
        strokeWidth={picked ? 2.5 : 2}
        color={picked ? theme.colors.primary : color}
      />
      {line ? <Path path={line} style="stroke" strokeWidth={2} color={color} /> : null}
      <SkText
        x={n.x + 20}
        y={n.y + 22}
        text={lessonNode(state)}
        font={font(12)}
        color={theme.colors.onSurfaceVariant}
      />
      <SkText x={n.x + 20} y={n.y + 40} text={cut(x.title, 19)} font={font(13)} color={theme.colors.onSurface} />
    </Group>
  );
});

const CertNode = memo(function CertNode(props: {
  theme: MD3Theme;
  n: Placed;
  title: string;
  pips: CertPip[];
  picked: boolean;
  opacity: number;
}) {
  const { n, picked, theme } = props;
  const accent = theme.colors.secondary;
  return (
    <Group opacity={props.opacity}>
      <RoundedRect
        x={n.x}
        y={n.y}
        width={NODE_W}
        height={NODE_H}
        r={NODE_H / 2}
        color={theme.colors.secondaryContainer}
        opacity={0.5}
      />
      <RoundedRect
        x={n.x}
        y={n.y}
        width={NODE_W}
        height={NODE_H}
        r={NODE_H / 2}
        style="stroke"
        strokeWidth={picked ? 2.5 : 1.5}
        color={picked ? theme.colors.primary : accent}
      />
      <SkText x={n.x + 18} y={n.y + 22} text={cut(props.title, 20)} font={font(13)} color={theme.colors.onSurface} />
      {props.pips.map((p, i) => {
        const cx = n.x + 26 + i * 26;
        const cy = n.y + NODE_H - 15;
        return (
          <Group key={p.letter}>
            <Circle cx={cx} cy={cy} r={9} color={p.color} opacity={p.filled ? 1 : 0.18} />
            <Circle cx={cx} cy={cy} r={9} style="stroke" strokeWidth={1.2} color={p.color} />
            <SkText
              x={cx - 3.5}
              y={cy + 4}
              text={p.letter}
              font={font(10)}
              color={p.filled ? theme.colors.surface : theme.colors.onSurface}
            />
          </Group>
        );
      })}
    </Group>
  );
});
