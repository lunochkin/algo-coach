import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import {
  type HostInstance,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  ScrollView,
  type ScrollViewInstance,
  View,
} from 'react-native';
import { useTheme } from 'react-native-paper';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { sectionOpened, sectionToggled } from '@algo-coach/core';
import { Heading } from '@/ui/rows';
import { Toggle } from '@/ui/toggle';
import { space } from '@/ui/tokens';

export interface Item {
  id: string;
  label: string;
}

/**
 * A long screen's sections, as the web's `useSections` holds them: which the
 * reader closed, the one they are in, and a jump that opens a section before
 * scrolling to it. Positions are measured against the scroll view, so a
 * section nested in other views reads the same. `register` names any view a
 * jump can reach, a lesson's `###` anchors included.
 */
export function useSections(items: Item[]) {
  const scroll = useRef<ScrollViewInstance>(null);
  const views = useRef(new Map<string, HostInstance>());
  const offset = useRef(0);
  const last = useRef(0);
  const trailing = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [closed, setClosed] = useState<string[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const atEnd = useRef(false);
  // the furthest the page scrolls: a jump past it overshoots and springs back
  const end = useRef<number | null>(null);
  // the section pressed stays marked until the reader drags the page: a jump
  // near the end lands where the end rule would mark the last section instead
  const jumped = useRef<string | null>(null);

  const at = useCallback(
    (id: string) =>
      new Promise<number | null>((resolve) => {
        const view = views.current.get(id);
        const host = scroll.current;
        if (!view || !host) return resolve(null);
        view.measureLayout(
          host as never,
          (_x: number, y: number) => resolve(y),
          () => resolve(null),
        );
      }),
    [],
  );

  const ids = items.map((item) => item.id).join(',');
  const mark = useCallback(async () => {
    const named = ids ? ids.split(',') : [];
    const ys = await Promise.all(named.map(at));
    // the section whose heading sits above the top fifth of the screen
    let found: string | null = named[0] ?? null;
    ys.forEach((y, i) => {
      if (y !== null && y <= offset.current + 120) found = named[i];
    });
    // at the end the last section is read, though its heading never reaches the top
    if (atEnd.current) found = named[named.length - 1] ?? found;
    setCurrent(jumped.current ?? found);
  }, [ids, at]);

  const onScroll = useCallback(
    (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
      offset.current = contentOffset.y;
      atEnd.current = contentOffset.y + layoutMeasurement.height >= contentSize.height - 2;
      end.current = Math.max(0, contentSize.height - layoutMeasurement.height);
      // throttled, with a trailing mark so the last position always reads
      if (trailing.current) clearTimeout(trailing.current);
      trailing.current = setTimeout(() => void mark(), 150);
      const now = Date.now();
      if (now - last.current < 120) return;
      last.current = now;
      void mark();
    },
    [mark],
  );

  const jump = useCallback(
    (id: string, animated = true) => {
      setClosed((was) => sectionOpened(was, id));
      if (ids.split(',').includes(id)) {
        jumped.current = id;
        setCurrent(id);
      }
      // a closed section lays out its body on the next frame
      requestAnimationFrame(
        () =>
          void at(id).then((y) => {
            if (y === null) return;
            const want = Math.max(0, y - 8);
            const to = end.current === null ? want : Math.min(want, end.current);
            // a section already in place stays put: a move shorter than a line reads as a twitch
            if (Math.abs(to - offset.current) < 24) return;
            scroll.current?.scrollTo({ y: to, animated });
          }),
      );
    },
    [at, ids],
  );

  const register = useCallback(
    (id: string) => (view: HostInstance | null) => {
      if (view) views.current.set(id, view);
      else views.current.delete(id);
    },
    [],
  );

  const onScrollBeginDrag = useCallback(() => {
    jumped.current = null;
  }, []);

  return {
    items,
    current,
    scroll,
    onScroll,
    onScrollBeginDrag,
    jump,
    register,
    closed: (id: string) => closed.includes(id),
    toggle: (id: string) => setClosed((was) => sectionToggled(was, id)),
  };
}

export type Sections = ReturnType<typeof useSections>;

/**
 * The sections of a long screen in one row under its header, which stays in
 * place as the screen scrolls. One section has nothing to jump between.
 */
export function SectionBar({ sections }: { sections: Pick<Sections, 'items' | 'current' | 'jump'> }) {
  const theme = useTheme();
  const row = useRef<ScrollViewInstance>(null);
  const chips = useRef(new Map<string, { x: number; width: number }>());
  const [view, setView] = useState({ x: 0, width: 0, content: 0 });

  // the row follows the marked section, as the web's does: `pages.md`
  useEffect(() => {
    const chip = sections.current ? chips.current.get(sections.current) : undefined;
    if (!chip || !view.width) return;
    const pad = space[6];
    if (chip.x - pad < view.x) row.current?.scrollTo({ x: Math.max(0, chip.x - pad), animated: true });
    else if (chip.x + chip.width + pad > view.x + view.width)
      row.current?.scrollTo({ x: chip.x + chip.width + pad - view.width, animated: true });
    // the scroll position is read, not followed: a reader scrolling the row keeps it
  }, [sections.current, view.width]);

  if (sections.items.length < 2) return null;
  const ground = theme.colors.background;
  return (
    <View style={{ borderBottomWidth: 1, borderColor: theme.colors.outlineVariant }}>
      <ScrollView
        ref={row}
        horizontal
        showsHorizontalScrollIndicator={false}
        scrollEventThrottle={32}
        onLayout={(e) => {
          const width = e.nativeEvent.layout.width;
          setView((v) => ({ ...v, width }));
        }}
        onContentSizeChange={(content) => setView((v) => ({ ...v, content }))}
        onScroll={(e) => {
          const x = e.nativeEvent.contentOffset.x;
          setView((v) => ({ ...v, x }));
        }}
        contentContainerStyle={{ gap: space[1.5], paddingHorizontal: space[4], paddingVertical: space[2] }}
      >
        {sections.items.map((item) => (
          <View
            key={item.id}
            onLayout={(e) => chips.current.set(item.id, { x: e.nativeEvent.layout.x, width: e.nativeEvent.layout.width })}
          >
            <Toggle on={sections.current === item.id} onPress={() => sections.jump(item.id)}>
              {item.label}
            </Toggle>
          </View>
        ))}
      </ScrollView>
      {/* a faded edge says the row goes on past it */}
      {view.x > 1 ? <Fade side="left" ground={ground} /> : null}
      {view.x + view.width < view.content - 1 ? <Fade side="right" ground={ground} /> : null}
    </View>
  );
}

function Fade({ side, ground }: { side: 'left' | 'right'; ground: string }) {
  const id = `fade-${side}`;
  return (
    <View pointerEvents="none" style={{ position: 'absolute', top: 0, bottom: 0, width: space[6], [side]: 0 }}>
      <Svg width="100%" height="100%">
        <Defs>
          <LinearGradient id={id} x1={side === 'left' ? '1' : '0'} y1="0" x2={side === 'left' ? '0' : '1'} y2="0">
            <Stop offset="0" stopColor={ground} stopOpacity="0" />
            <Stop offset="1" stopColor={ground} stopOpacity="1" />
          </LinearGradient>
        </Defs>
        <Rect width="100%" height="100%" fill={`url(#${id})`} />
      </Svg>
    </View>
  );
}

/**
 * One section of a long screen: its heading closes it. Prose reads bare under
 * it, so a code block is the only box, and a list brings its own panel.
 */
export function PageSection(props: {
  of: Sections;
  id: string;
  title: string;
  count?: number;
  aside?: ReactNode;
  children: ReactNode;
}) {
  const closed = props.of.closed(props.id);
  return (
    <View ref={props.of.register(props.id)} collapsable={false} style={{ gap: space[2] }}>
      <Heading
        title={props.title}
        count={props.count}
        aside={props.aside}
        closed={closed}
        onToggle={() => props.of.toggle(props.id)}
      />
      {closed ? null : props.children}
    </View>
  );
}
